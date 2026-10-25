import os
import sys
from assistant.text_io import configure_unicode_streams

# Configure redirected Windows stdout before importing libraries or starting workers.
configure_unicode_streams()

import time
import json
import asyncio
import threading
import re
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
from storage.reminders import create_reminder, claim_due_reminders

# Internal imports
from storage.database import init_db, get_connection, get_all_settings, set_setting, log_audit
from assistant.state_machine import StateMachine, AssistantState
from assistant.email_drafts import EmailDrafts
from voice.audio_capture import AudioCapture
from voice.stt_whisper import FasterWhisperSTT
from wakeword.porcupine_engine import PorcupineWakeWordEngine
from tts.speech_synth import TextToSpeechEngine
from commands.parser import CommandParser
from commands.executor import CommandExecutor
from automation.routine_runner import RoutineRunner
from providers.llm_manager import LLMManager
from windows.system_info import get_system_metrics
from windows.power import execute_shutdown, execute_restart

# Initialize components
init_db()

state_machine = StateMachine(AssistantState.IDLE)
audio_capture = AudioCapture()
whisper_stt = FasterWhisperSTT(model_size="base")
wake_engine = PorcupineWakeWordEngine()
tts_engine = TextToSpeechEngine()
routine_runner = RoutineRunner(tts_engine=tts_engine, notifier=lambda title, body: broadcast_sync({"type": "notification", "title": title, "body": body}))
command_executor = CommandExecutor(routine_runner=routine_runner)
llm_manager = LLMManager()
email_drafts = EmailDrafts(llm_manager)

# Connected WebSocket clients
connected_websockets: List[WebSocket] = []
ws_lock = threading.Lock()
main_loop = None
interaction_lock = threading.Lock()
command_lock = threading.Lock()
shutdown_event = threading.Event()
voice_cancelled = threading.Event()
pending_power = None
pending_power_lock = threading.Lock()

def publish_settings():
    settings = {k: v for k, v in get_all_settings().items() if not k.endswith(('_api_key', '_access_key'))}
    broadcast_sync({"type": "settings_changed", "settings": settings})
    broadcast_sync({"type": "wake_status", "status": wake_engine.status, "error": wake_engine.error_message})

def speak(text):
    settings = get_all_settings()
    tts_engine.speak(text, voice_id=settings.get('tts_voice_id') or None,
                     rate=int(settings.get('tts_rate', '180')), volume=float(settings.get('tts_volume', '1')))

def reminder_worker():
    global pending_power
    while not shutdown_event.wait(1):
        try:
            with pending_power_lock:
                expired = pending_power is not None and pending_power['expires'] < time.monotonic()
                if expired:
                    pending_power = None
            if expired:
                state_machine.transition_to(AssistantState.IDLE, {"pending_confirmation": None, "response": "Power confirmation expired. No action was taken."})
            for reminder in claim_due_reminders():
                broadcast_sync({"type": "reminder_due", "reminder": reminder})
                speak(f"Reminder: {reminder['title']}")
                log_audit('REMINDER_DUE', reminder['title'], 'SUCCESS')
        except Exception as exc:
            print(f'[Reminders] {exc}')

def resume_wake():
    if not shutdown_event.is_set() and not interaction_lock.locked() and not tts_engine.is_speaking:
        settings = get_all_settings()
        if settings.get('wake_word_enabled') == 'true' and settings.get('auto_conversation') != 'true' and wake_engine.status == 'READY':
            device = settings.get('selected_mic_device', '')
            wake_engine.start_listening(on_wake_detected, int(device) if device else None)
    broadcast_sync({"type": "wake_status", "status": wake_engine.status, "error": wake_engine.error_message})

def start_voice():
    if shutdown_event.is_set() or tts_engine.is_speaking or not interaction_lock.acquire(blocking=False):
        return False
    voice_cancelled.clear()
    threading.Thread(target=process_voice_interaction, daemon=True).start()
    return True

def schedule_auto_listen():
    def delayed():
        if not shutdown_event.wait(0.8) and get_all_settings().get('auto_conversation') == 'true':
            start_voice()
    threading.Thread(target=delayed, daemon=True).start()


def broadcast_sync(payload: Dict[str, Any]):
    """Thread-safe broadcast helper to all connected WebSockets."""
    if main_loop is None or main_loop.is_closed():
        return
    text_data = json.dumps(payload)
    with ws_lock:
        clients = list(connected_websockets)
    for ws in clients:
        try:
            asyncio.run_coroutine_threadsafe(ws.send_text(text_data), main_loop)
        except Exception:
            pass

# State Machine callback
def on_state_changed(new_state: AssistantState, context: Dict[str, Any]):
    broadcast_sync({
        "type": "state_change",
        "state": new_state.value,
        "context": context
    })

state_machine.subscribe(on_state_changed)

# Audio waveform RMS reactivity callback
def on_waveform_level(rms_level: float):
    broadcast_sync({
        "type": "waveform",
        "level": rms_level
    })

audio_capture.set_waveform_callback(on_waveform_level)

# TTS state callbacks
def on_tts_start():
    wake_engine.stop_listening()
    state_machine.transition_to(AssistantState.SPEAKING)

def on_tts_end():
    settings = get_all_settings()
    auto_conv = settings.get("auto_conversation", "false") == "true"
    if state_machine.context.get('pending_confirmation'):
        state_machine.transition_to(AssistantState.AWAITING_CONFIRMATION)
        return
    state_machine.transition_to(AssistantState.IDLE)
    if auto_conv:
        schedule_auto_listen()
    else:
        resume_wake()

tts_engine.set_callbacks(on_tts_start, on_tts_end)

# Wake Word trigger callback
def on_wake_detected():
    state_machine.transition_to(AssistantState.WAKE_DETECTED, {"transcript": "Hey Oska"})
    broadcast_sync({"type": "wake_detected"})
    start_voice()

# Process full voice command interaction
def process_voice_interaction():
    try:
        wake_engine.stop_listening()
        settings = get_all_settings()
        device = settings.get('selected_mic_device', '')
        audio_capture.set_device(int(device) if device else None)
        state_machine.transition_to(AssistantState.LISTENING, {"transcript": "", "response": "", "last_error": None})
        audio_capture.start_recording()
        has_speech = audio_capture.wait_for_utterance(shutdown_event, voice_cancelled)
        audio_data = audio_capture.stop_recording()
        if shutdown_event.is_set() or voice_cancelled.is_set():
            state_machine.transition_to(AssistantState.IDLE)
            return
        state_machine.transition_to(AssistantState.TRANSCRIBING)
        if len(audio_data) > 0:
            language = settings.get('speech_language', 'auto')
            whisper_stt.set_groq_api_key(settings.get('groq_api_key') or settings.get('llm_api_key'))
            text = whisper_stt.transcribe(audio_data, language=None if language == 'auto' else language)
            if text and text.strip():
                handle_command_text(text)
                return
        state_machine.transition_to(AssistantState.IDLE, {"last_error": "No speech recognized. Please try again.", "response": "No speech recognized. Please try again."})
    except Exception as exc:
        state_machine.transition_to(AssistantState.ERROR, {"last_error": str(exc), "response": str(exc)})
    finally:
        audio_capture.close()
        interaction_lock.release()
        resume_wake()
        if not tts_engine.is_speaking and not state_machine.context.get('pending_confirmation'):
            if get_all_settings().get('auto_conversation') == 'true':
                schedule_auto_listen()


def handle_command_text(text: str) -> Dict[str, Any]:
    with command_lock:
        try:
            return _handle_command_text(text)
        except Exception as exc:
            log_audit("COMMAND_ERROR", text, "FAILED")
            state_machine.transition_to(AssistantState.ERROR, {"last_error": str(exc), "response": str(exc)})
            return {"status": "FAILED", "response": str(exc)}

def _handle_command_text(text: str) -> Dict[str, Any]:
    global pending_power
    state_machine.transition_to(AssistantState.THINKING, {"transcript": text})
    
    # Exact user-defined trigger phrases take precedence over general parsing.
    conn = get_connection()
    try:
        routine = conn.execute("SELECT id FROM routines WHERE enabled = 1 AND lower(trim(trigger_phrase)) = ? AND trim(trigger_phrase) != ''", (text.strip().lower(),)).fetchone()
    finally:
        conn.close()
    draft_operation = email_drafts.classify(text)
    if draft_operation:
        parsed = {'intent':'email_draft', 'args':{'operation':draft_operation}}
    elif re.search(r'^(stop listening|stop conversation|stop talking|conversation off|කතා කරන එක නවත්තන්න)$', text.strip(), re.I):
        parsed = {'intent':'stop_conversation','args':{}}
    else:
        parsed = {"intent": "trigger_routine", "args": {"routine_id": routine['id']}} if routine else CommandParser.parse(text)
    intent = parsed.get("intent")

    if intent == 'email_draft':
        exec_result = email_drafts.handle(text, get_all_settings(), parsed['args']['operation'])
        draft = exec_result['data']['email_draft']
        broadcast_sync({'type':'email_draft_changed','draft':draft})
        if exec_result['data'].get('open_requested'):
            open_email_draft()
            exec_result['response'] = 'අලුත්ම draft එක Gmail එකේ ඇරියා. යවන්න කලින් ලිපිනයයි message එකයි බලන්න.' if re.search(r'[\u0D80-\u0DFF]|\b(karanna|arinna)\b', text, re.I) else 'Opened your latest draft in Gmail. Review the recipient and message before sending.'
            exec_result['spoken_response'] = exec_result['response']
    elif intent == 'stop_conversation':
        set_setting('auto_conversation', 'false')
        publish_settings()
        exec_result = {'status':'SUCCESS','response':'Continuous conversation stopped.','spoken_response':'Continuous conversation stopped.'}
    elif intent == "conversation":
        # Layer 2: LLM or conversational intelligence
        settings = get_all_settings()
        response_text = llm_manager.generate_response(text, settings)
        exec_result = {
            "intent": "conversation",
            "status": "SUCCESS",
            "response": response_text,
            "spoken_response": response_text
        }
    else:
        state_machine.transition_to(AssistantState.EXECUTING)
        exec_result = command_executor.execute(parsed)

    # Save to chat history
    try:
        conn = get_connection()
        conn.execute("INSERT INTO chat_history (role, content, command_intent, status, created_at) VALUES (?, ?, ?, ?, ?)",
                     ("user", text, intent, "SUCCESS", time.time()))
        conn.execute("INSERT INTO chat_history (role, content, command_intent, status, created_at) VALUES (?, ?, ?, ?, ?)",
                     ("assistant", exec_result.get("response", ""), intent, exec_result.get("status", "SUCCESS"), time.time()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Main] Chat history save error: {e}")

    confirmation = exec_result.get('data') if exec_result.get('status') == 'REQUIRES_CONFIRMATION' else None
    with pending_power_lock:
        pending_power = {"action": confirmation['pending_action'], "expires": time.monotonic() + 60} if confirmation else None
    state_machine.update_context({"response": exec_result.get('response', ''), "pending_confirmation": confirmation})
    if exec_result.get('spoken_response'):
        speak(exec_result['spoken_response'])
    else:
        state_machine.transition_to(AssistantState.AWAITING_CONFIRMATION if confirmation else AssistantState.SUCCESS)

    broadcast_sync({
        "type": "command_result",
        "result": exec_result,
        "transcript": text
    })

    return exec_result

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    shutdown_event.clear()
    settings = get_all_settings()
    whisper_stt.model_size = settings.get('stt_model', 'base')
    whisper_stt.set_groq_api_key(settings.get('groq_api_key') or settings.get('llm_api_key'))
    wake_engine.configure(settings.get('porcupine_access_key', ''), settings.get('porcupine_keyword_path', ''), float(settings.get('porcupine_sensitivity', '.5')))
    resume_wake()
    threading.Thread(target=reminder_worker, daemon=True).start()
    if settings.get('auto_conversation') == 'true':
        start_voice()
    yield
    shutdown_event.set()
    wake_engine.close()
    audio_capture.close()
    tts_engine.stop()

app = FastAPI(title="OSKA NEXUS Desktop Core", lifespan=lifespan)

ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://tauri.localhost", "https://tauri.localhost", "tauri://localhost"]

@app.middleware('http')
async def check_origin(request, call_next):
    origin = request.headers.get('origin')
    if origin and origin not in ALLOWED_ORIGINS:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={'detail':'Untrusted request origin.'})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class CommandRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, str]

class ConfirmationRequest(BaseModel):
    action: str
    confirmed: bool

class RoutineCreateRequest(BaseModel):
    id: str
    name: str
    description: str
    trigger_phrase: str
    actions: List[Dict[str, Any]]

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get('origin')
    if origin and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    with ws_lock:
        connected_websockets.append(websocket)
    try:
        # Send initial full state
        await websocket.send_json({
            "type": "initial_state",
            "state": state_machine.current_state.value,
            "context": state_machine.context,
            "wake_status": wake_engine.status,
            "wake_error": wake_engine.error_message
        })
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except (WebSocketDisconnect, ValueError, RuntimeError):
        pass
    finally:
        with ws_lock:
            if websocket in connected_websockets:
                connected_websockets.remove(websocket)

# REST Routes
@app.get("/api/state")
def get_state():
    return {
        "state": state_machine.current_state.value,
        "context": state_machine.context,
        "wake_status": wake_engine.status,
        "wake_error": wake_engine.error_message
    }

@app.get("/api/settings")
def api_get_settings():
    return get_all_settings()

@app.post("/api/settings")
def api_update_settings(req: SettingsUpdateRequest):
    previous = get_all_settings()
    settings = {**previous, **req.settings}
    try:
        if not 80 <= int(settings.get('tts_rate', '180')) <= 400:
            raise ValueError('Speech rate must be between 80 and 400.')
        if not 0 <= float(settings.get('tts_volume', '1')) <= 1 or not 0 <= float(settings.get('porcupine_sensitivity', '.5')) <= 1:
            raise ValueError('Volume and sensitivity must be between 0 and 1.')
        device = settings.get('selected_mic_device', '')
        if device:
            int(device)
        if settings.get('stt_model', 'base') not in ['tiny', 'base', 'small', 'medium', 'large-v3']:
            raise ValueError('Unsupported speech recognition model.')
        if settings.get('speech_language', 'auto') not in ['auto', 'si', 'en']:
            raise ValueError('Choose Auto, Sinhala or English for speech recognition.')
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc))
    if interaction_lock.locked():
        raise HTTPException(409, 'Wait for the current voice interaction to finish before saving settings.')
    for k, v in req.settings.items():
        set_setting(k, v)
    audio_capture.set_device(int(device) if device else None)
    whisper_stt.set_groq_api_key(settings.get('groq_api_key') or settings.get('llm_api_key'))
    if previous.get('stt_model') != settings.get('stt_model'):
        whisper_stt.model_size = settings.get('stt_model', 'base')
        whisper_stt._model = None
    wake_keys = ['porcupine_access_key', 'porcupine_keyword_path', 'porcupine_sensitivity']
    if any(previous.get(k) != settings.get(k) for k in wake_keys):
        wake_engine.configure(settings.get('porcupine_access_key', ''), settings.get('porcupine_keyword_path', ''), float(settings.get('porcupine_sensitivity', '.5')))
    if settings.get('wake_word_enabled') != 'true':
        wake_engine.stop_listening()
    resume_wake()
    publish_settings()
    return {"status": "SUCCESS", "settings": settings}

@app.post("/api/command")
def api_execute_command(req: CommandRequest):
    if not req.text.strip():
        raise HTTPException(422, 'Command cannot be blank.')
    return handle_command_text(req.text.strip())

@app.post("/api/voice/listen")
def api_start_voice():
    if not start_voice():
        raise HTTPException(409, 'Assistant is busy. Wait for speech or recording to finish.')
    return {"status": "SUCCESS", "message": "Voice interaction started"}

@app.post('/api/voice/stop')
def api_stop_voice():
    voice_cancelled.set()
    set_setting('auto_conversation', 'false')
    tts_engine.stop()
    publish_settings()
    return {'status':'SUCCESS'}

@app.post("/api/wake/toggle")
def api_toggle_wake():
    settings = get_all_settings()
    current = settings.get("wake_word_enabled", "false") == "true"
    new_state = not current
    set_setting("wake_word_enabled", "true" if new_state else "false")

    if new_state:
        if wake_engine.status not in ['READY', 'LISTENING']:
            set_setting('wake_word_enabled', 'false')
            publish_settings()
            raise HTTPException(409, wake_engine.error_message or 'Configure your wake word first.')
        resume_wake()
    else:
        wake_engine.stop_listening()
    publish_settings()
    return {"enabled": new_state, "listening": wake_engine.status == 'LISTENING', "status": wake_engine.status}

@app.post("/api/auto_conversation/toggle")
def api_toggle_auto_conversation():
    settings = get_all_settings()
    current = settings.get("auto_conversation", "false") == "true"
    new_val = not current
    set_setting("auto_conversation", "true" if new_val else "false")
    if new_val:
        wake_engine.stop_listening()
        start_voice()
    else:
        resume_wake()
    publish_settings()
    return {"auto_conversation": new_val}

@app.get("/api/audio/devices")
def api_get_audio_devices():
    return AudioCapture.list_input_devices()

@app.get("/api/tts/voices")
def api_get_tts_voices():
    return tts_engine.get_available_voices()

@app.post("/api/tts/test")
def api_test_voice():
    speak("This is OSKA NEXUS. Voice output is ready.")
    return {"status": "SUCCESS"}

@app.get("/api/chat/history")
def api_get_chat_history():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM (SELECT * FROM chat_history ORDER BY id DESC LIMIT 100) ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.delete("/api/chat/history")
def api_clear_chat_history():
    conn = get_connection()
    conn.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()
    return {"status": "SUCCESS"}

@app.get("/api/metrics")
def api_get_metrics():
    return get_system_metrics()

@app.get("/api/routines")
def api_get_routines():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM routines ORDER BY created_at ASC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["actions"] = json.loads(d["actions_json"])
        result.append(d)
    return result

@app.post("/api/routines")
def api_create_routine(req: RoutineCreateRequest):
    if not req.id.strip() or not req.name.strip() or not req.actions:
        raise HTTPException(422, 'Routine ID, name and at least one action are required.')
    for step in req.actions:
        if step.get('type') not in ['open_app', 'open_url', 'set_volume', 'notify', 'speak_time', 'timer']:
            raise HTTPException(422, 'Unsupported routine action.')
        if step['type'] == 'timer':
            try:
                if not 0 < float(step.get('target', '')) <= 10080: raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(422, 'Timer must be between 0 and 10080 minutes.')
        if step['type'] == 'set_volume':
            try:
                if not 0 <= int(step.get('target', '')) <= 100: raise ValueError()
            except (ValueError, TypeError):
                raise HTTPException(422, 'Routine volume must be between 0 and 100.')
    conn = get_connection()
    if conn.execute('SELECT id FROM routines WHERE id = ?', (req.id,)).fetchone():
        conn.close()
        raise HTTPException(409, 'A routine with that ID already exists.')
    conn.execute("""
    INSERT INTO routines (id, name, description, trigger_phrase, actions_json, enabled, created_at)
    VALUES (?, ?, ?, ?, ?, 1, ?)
    """, (req.id, req.name, req.description, req.trigger_phrase, json.dumps(req.actions), time.time()))
    conn.commit()
    conn.close()
    return {"status": "SUCCESS", "id": req.id}

@app.post("/api/routines/{routine_id}/run")
def api_run_routine(routine_id: str):
    with command_lock:
        res = routine_runner.run_routine(routine_id)
    if res.get("spoken_response"):
        speak(res["spoken_response"])
    return res

@app.get("/api/reminders")
def api_get_reminders():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reminders ORDER BY due_time ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

class ReminderRequest(BaseModel):
    title: str = Field(min_length=1, max_length=1000)
    due_time: Optional[float] = None

class ReminderUpdate(BaseModel):
    completed: bool

@app.post("/api/reminders")
def api_create_reminder(req: ReminderRequest):
    try:
        return create_reminder(req.title, req.due_time)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

def mutate_record(table, record_id, query, values=()):
    conn = get_connection()
    try:
        if not conn.execute(f'SELECT id FROM {table} WHERE id = ?', (record_id,)).fetchone():
            raise HTTPException(404, 'Item not found.')
        conn.execute(query, (*values, record_id))
        conn.commit()
    finally:
        conn.close()
    return {"status": "SUCCESS"}

@app.patch('/api/reminders/{record_id}')
def api_update_reminder(record_id: int, req: ReminderUpdate):
    return mutate_record('reminders', record_id, 'UPDATE reminders SET completed = ? WHERE id = ?', (int(req.completed),))

@app.delete('/api/reminders/{record_id}')
def api_delete_reminder(record_id: int):
    return mutate_record('reminders', record_id, 'DELETE FROM reminders WHERE id = ?')

@app.get("/api/notes")
def api_get_notes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

class NoteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100000)

@app.post('/api/notes')
def api_create_note(req: NoteRequest):
    if not req.title.strip() or not req.content.strip():
        raise HTTPException(422, 'Title and content are required.')
    conn = get_connection()
    try:
        cursor = conn.execute('INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)', (req.title.strip(), req.content.strip(), time.time(), time.time()))
        conn.commit()
        return {"status": "SUCCESS", "id": cursor.lastrowid}
    finally:
        conn.close()

@app.put('/api/notes/{record_id}')
def api_update_note(record_id: int, req: NoteRequest):
    if not req.title.strip() or not req.content.strip():
        raise HTTPException(422, 'Title and content are required.')
    return mutate_record('notes', record_id, 'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?', (req.title.strip(), req.content.strip(), time.time()))

@app.delete('/api/notes/{record_id}')
def api_delete_note(record_id: int):
    return mutate_record('notes', record_id, 'DELETE FROM notes WHERE id = ?')

@app.get('/api/audit')
def api_audit():
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200')]
    finally:
        conn.close()

class EmailDraftRequest(BaseModel):
    recipient: str = Field(default='', max_length=250)
    subject: str = Field(max_length=250)
    body: str = Field(min_length=1, max_length=20000)
    signature: str = Field(default='', max_length=250)

@app.get('/api/email/draft')
def api_get_email_draft():
    return {'draft':email_drafts.current()}

@app.put('/api/email/draft')
def api_save_email_draft(req: EmailDraftRequest):
    try:
        draft = email_drafts.save(req.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    broadcast_sync({'type':'email_draft_changed', 'draft':draft})
    return {'draft':draft}

@app.post('/api/email/open')
def open_email_draft():
    from windows.apps import open_url
    draft = email_drafts.current()
    if not draft:
        raise HTTPException(409, 'Create an email draft first.')
    ok, _ = open_url(email_drafts.gmail_url(draft))
    if not ok:
        raise HTTPException(503, 'Could not open Gmail. Check your default browser.')
    log_audit('OPEN_EMAIL_DRAFT', f"Draft {draft['id']}", 'SUCCESS')
    return {'status':'SUCCESS', 'message':'Opened the latest draft in Gmail for review.'}

@app.post("/api/power/confirm")
def api_confirm_power(req: ConfirmationRequest):
    global pending_power
    with pending_power_lock:
        if pending_power and pending_power['expires'] < time.monotonic():
            pending_power = None
            state_machine.transition_to(AssistantState.IDLE, {"pending_confirmation": None})
        if not pending_power or pending_power['action'] != req.action or pending_power['expires'] < time.monotonic():
            raise HTTPException(409, 'No matching pending power action, or confirmation expired.')
        pending_power = None
    state_machine.transition_to(AssistantState.IDLE, {"pending_confirmation": None})
    if not req.confirmed:
        log_audit('POWER_CONFIRMATION', req.action, 'CANCELLED')
        return {"status": "CANCELLED", "message": "Power action cancelled."}
    action = execute_shutdown if req.action == 'request_shutdown' else execute_restart
    ok, msg = action(True)
    log_audit('POWER_CONFIRMATION', req.action, 'SUCCESS' if ok else 'FAILED')
    return {"status": "SUCCESS" if ok else "FAILED", "message": msg}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get('OSKA_PORT', '8765')), log_level="info")
