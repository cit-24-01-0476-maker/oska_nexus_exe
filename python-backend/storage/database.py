import sqlite3
import json
import os
import time
from typing import List, Dict, Any, Optional

# Packaged applications need a writable per-user data directory.
DATA_DIR = os.environ.get("OSKA_DATA_DIR") or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "OSKA NEXUS")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "oska_nexus.db")
legacy_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "oska_nexus.db")
if not os.path.exists(DB_PATH) and os.path.isfile(legacy_db) and not os.environ.get("OSKA_DATA_DIR"):
    import shutil
    shutil.copy2(legacy_db, DB_PATH)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Chat history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        command_intent TEXT,
        status TEXT,
        created_at REAL NOT NULL
    )
    """)

    # Routines
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routines (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        trigger_phrase TEXT,
        actions_json TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        created_at REAL NOT NULL
    )
    """)

    # Reminders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        due_time REAL NOT NULL,
        completed INTEGER DEFAULT 0,
        created_at REAL NOT NULL
    )
    """)

    if 'notified' not in [r[1] for r in cursor.execute('PRAGMA table_info(reminders)')]:
        cursor.execute('ALTER TABLE reminders ADD COLUMN notified INTEGER DEFAULT 0')

    # Notes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    )
    """)

    # Audit Logs
    cursor.execute('''CREATE TABLE IF NOT EXISTS email_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL DEFAULT '', subject TEXT NOT NULL,
        body TEXT NOT NULL, signature TEXT NOT NULL DEFAULT '', updated_at REAL NOT NULL
    )''')

    # Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        details TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at REAL NOT NULL
    )
    """)

    # Default settings seed
    default_settings = {
        "auto_conversation": "false",
        "selected_mic_device": "",
        "display_name": "",
        "speech_language": "auto",
        "wake_word_enabled": "false",
        "porcupine_access_key": "",
        "porcupine_keyword_path": "",
        "porcupine_sensitivity": "0.5",
        "stt_model": "base",
        "tts_voice_id": "",
        "tts_rate": "180",
        "tts_volume": "1.0",
        "llm_provider": "local_rules", # local_rules, ollama, openai, gemini
        "llm_model": "gpt-4o-mini",
        "llm_api_key": "",
        "xai_api_key": "",
        "xai_model": "grok-4.7",
        "ollama_endpoint": "http://localhost:11434",
        "minimize_to_tray": "true",
        "start_with_windows": "false",
        "global_shortcut": "Ctrl+Shift+Space",
        "low_power_mode": "false"
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Pre-seed default routines
    seed_routines = [
        {
            "id": "routine-coding",
            "name": "Coding Mode",
            "description": "Prepares development workspace with VS Code and GitHub",
            "trigger_phrase": "coding mode",
            "actions_json": json.dumps([
                {"type": "open_app", "target": "code", "label": "Launch Visual Studio Code"},
                {"type": "open_url", "target": "https://github.com", "label": "Open GitHub"},
                {"type": "notify", "target": "Coding mode initiated. Let's build.", "label": "System notification"}
            ]),
            "enabled": 1,
            "created_at": time.time()
        },
        {
            "id": "routine-study",
            "name": "Study Mode",
            "description": "Opens reference workspace and study timer",
            "trigger_phrase": "study mode",
            "actions_json": json.dumps([
                {"type": "open_app", "target": "notepad", "label": "Launch Study Notepad"},
                {"type": "set_volume", "target": "25", "label": "Set Audio Volume to 25%"},
                {"type": "timer", "target": "25", "label": "Start 25-minute focus timer"},
                {"type": "notify", "target": "Study mode active. Focus timer: 25 mins.", "label": "Study Alert"}
            ]),
            "enabled": 1,
            "created_at": time.time()
        },
        {
            "id": "routine-meeting",
            "name": "Meeting Mode",
            "description": "Prepares desktop for meetings",
            "trigger_phrase": "meeting mode",
            "actions_json": json.dumps([
                {"type": "open_app", "target": "notepad", "label": "Open Meeting Notes"},
                {"type": "notify", "target": "Meeting mode activated. Ready for meeting notes.", "label": "Meeting Ready"}
            ]),
            "enabled": 1,
            "created_at": time.time()
        },
        {
            "id": "routine-daily",
            "name": "Daily Start",
            "description": "Morning briefing and daily essentials",
            "trigger_phrase": "start my day",
            "actions_json": json.dumps([
                {"type": "speak_time", "target": "", "label": "Announce System Time"},
                {"type": "open_url", "target": "https://calendar.google.com", "label": "Open Calendar"},
                {"type": "notify", "target": "Good day! OSKA NEXUS is at your command.", "label": "Greeting"}
            ]),
            "enabled": 1,
            "created_at": time.time()
        }
    ]

    for r in seed_routines:
        cursor.execute("""
        INSERT OR IGNORE INTO routines (id, name, description, trigger_phrase, actions_json, enabled, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r["id"], r["name"], r["description"], r["trigger_phrase"], r["actions_json"], r["enabled"], r["created_at"]))

    # Upgrade untouched defaults from earlier installations without replacing
    # routines the user has customized.
    study = next(r for r in seed_routines if r['id'] == 'routine-study')
    desired_actions = json.loads(study['actions_json'])
    old_actions = [a for a in desired_actions if a['type'] != 'timer']
    row = cursor.execute("SELECT actions_json FROM routines WHERE id = 'routine-study'").fetchone()
    if row and json.loads(row['actions_json']) == old_actions:
        cursor.execute("UPDATE routines SET actions_json = ? WHERE id = 'routine-study'", (study['actions_json'],))
    cursor.execute("UPDATE routines SET description = ? WHERE id = 'routine-coding' AND description = ?",
                   ('Prepares development workspace with VS Code and GitHub',
                    'Prepares development workspace with VS Code, browser docs, and focus timer'))

    conn.commit()
    conn.close()

# Helper queries
def get_all_settings() -> Dict[str, str]:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def log_audit(action_type: str, details: str, status: str):
    conn = get_connection()
    conn.execute("INSERT INTO audit_logs (action_type, details, status, created_at) VALUES (?, ?, ?, ?)",
                 (action_type, details, status, time.time()))
    conn.commit()
    conn.close()
