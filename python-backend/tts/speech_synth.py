import pyttsx3
import threading
import queue
import re
import os
import asyncio
import tempfile
from typing import List, Dict, Optional, Callable

try:
    import edge_tts
    import pygame
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

class TextToSpeechEngine:
    def __init__(self):
        self._queue = queue.Queue()
        self._speaking = False
        self._lock = threading.Lock()
        self._on_start_callback: Optional[Callable[[], None]] = None
        self._on_end_callback: Optional[Callable[[], None]] = None
        self._mixer_initialized = False
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def set_callbacks(self, on_start: Callable[[], None], on_end: Callable[[], None]):
        self._on_start_callback = on_start
        self._on_end_callback = on_end

    def get_available_voices(self) -> List[Dict[str, str]]:
        result = []
        if EDGE_TTS_AVAILABLE:
            result.append({"id": "si-LK-ThiliniNeural", "name": "Thilini (Sinhala Neural - Female)", "languages": ["si"], "gender": "Female"})
            result.append({"id": "si-LK-SameeraNeural", "name": "Sameera (Sinhala Neural - Male)", "languages": ["si"], "gender": "Male"})
            result.append({"id": "en-GB-SoniaNeural", "name": "Sonia (British English Neural - Female)", "languages": ["en"], "gender": "Female"})
            result.append({"id": "en-US-JennyNeural", "name": "Jenny (US English Neural - Female)", "languages": ["en"], "gender": "Female"})

        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for v in voices:
                result.append({
                    "id": v.id,
                    "name": f"{v.name} (Windows SAPI5)",
                    "languages": getattr(v, "languages", ["en"]),
                    "gender": getattr(v, "gender", "unknown")
                })
            engine.stop()
        except Exception as e:
            print(f"[TTS] Error listing local voices: {e}")
        return result

    def speak(self, text: str, voice_id: Optional[str] = None, rate: int = 180, volume: float = 1.0):
        if not text or not text.strip():
            return
        self._queue.put({
            "text": text.strip(),
            "voice_id": voice_id,
            "rate": rate,
            "volume": volume
        })

    def stop(self):
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break
        if EDGE_TTS_AVAILABLE and self._mixer_initialized:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass

    @property
    def is_speaking(self) -> bool:
        return self._speaking or not self._queue.empty()

    def _play_with_edge_tts(self, text: str, voice: str, rate=180, volume=1.0) -> bool:
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                tmp_path = f.name

            async def _generate():
                communicate = edge_tts.Communicate(text, voice, rate=f"{round((rate / 180 - 1) * 100):+d}%")
                await communicate.save(tmp_path)

            asyncio.run(_generate())

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                return False

            if not self._mixer_initialized:
                pygame.mixer.init()
                self._mixer_initialized = True

            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            import time
            start_wait = time.time()
            while pygame.mixer.music.get_busy() and time.time() - start_wait < 20.0:
                time.sleep(0.04)
            pygame.mixer.music.unload()

            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"[TTS] Edge-TTS playback error: {e}")
            return False

    def _play_with_sapi5(self, text: str, voice_id: Optional[str], rate: int, volume: float):
        try:
            engine = pyttsx3.init()
            if voice_id and "Neural" not in voice_id:
                engine.setProperty('voice', voice_id)
            else:
                voices = engine.getProperty('voices')
                for v in voices:
                    if 'hazel' in v.name.lower() or 'zira' in v.name.lower() or getattr(v, 'gender', '').lower() == 'female':
                        engine.setProperty('voice', v.id)
                        break
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[TTS] SAPI5 worker error: {e}")

    def _worker(self):
        while True:
            item = self._queue.get()
            if not item:
                continue

            text = item["text"]
            voice_id = item.get("voice_id")
            rate = item.get("rate", 180)
            volume = item.get("volume", 1.0)

            try:
                self._speaking = True
                if self._on_start_callback:
                    try:
                        self._on_start_callback()
                    except Exception:
                        pass

                # Detect if text contains Sinhala Unicode characters
                has_sinhala = bool(re.search(r'[\u0D80-\u0DFF]', text))

                played = False
                if EDGE_TTS_AVAILABLE and (not voice_id or "Neural" in voice_id):
                    if has_sinhala:
                        # Use Sinhala Neural voice
                        played = self._play_with_edge_tts(text, voice_id if voice_id and "Neural" in voice_id else "si-LK-ThiliniNeural", rate, volume)
                    else:
                        # Use English British or US Neural voice
                        neural_voice = voice_id if voice_id and "Neural" in voice_id else "en-GB-SoniaNeural"
                        played = self._play_with_edge_tts(text, neural_voice, rate, volume)

                # Fallback to local SAPI5 if edge-tts failed or offline
                if not played:
                    # Clean out sinhala chars if sending to SAPI5 to avoid silent skips
                    cleaned_text = re.sub(r'[\u0D80-\u0DFF]+', '', text).strip()
                    if not cleaned_text:
                        cleaned_text = "Action completed."
                    self._play_with_sapi5(cleaned_text, voice_id, rate, volume)

            except Exception as e:
                print(f"[TTS] Worker error: {e}")
            finally:
                self._speaking = False
                if self._on_end_callback:
                    try:
                        self._on_end_callback()
                    except Exception:
                        pass
                self._queue.task_done()
