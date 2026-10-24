"""Reminder scheduling shared by voice commands and the REST API."""
import re
import time
from datetime import datetime, timedelta
from storage.database import get_connection


def resolve_due_time(title: str, now=None) -> float:
    now = now or datetime.now()
    relative = re.search(r"\bin\s+(\d+)\s*(seconds?|minutes?|mins?|hours?|days?)\b", title, re.I)
    if relative:
        count, unit = int(relative[1]), relative[2].lower()
        seconds = 86400 if unit.startswith('day') else 3600 if unit.startswith('hour') else 60 if unit.startswith(('min',)) else 1
        return (now + timedelta(seconds=count * seconds)).timestamp()
    clock = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", title, re.I)
    if clock:
        hour, minute, period = int(clock[1]), int(clock[2] or 0), (clock[3] or '').lower()
        if minute > 59 or (period and not 1 <= hour <= 12) or (not period and hour > 23):
            raise ValueError('Enter a valid reminder time.')
        if period:
            hour = hour % 12 + (12 if period == 'pm' else 0)
        due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if 'tomorrow' in title.lower() or due <= now:
            due += timedelta(days=1)
        return due.timestamp()
    return (now + timedelta(hours=1)).timestamp()


def create_reminder(title: str, due_time=None):
    title = title.strip()
    if not title:
        raise ValueError('Reminder title is required.')
    due = float(due_time) if due_time is not None else resolve_due_time(title)
    if not due > time.time():
        raise ValueError('Reminder time must be in the future.')
    conn = get_connection()
    try:
        cursor = conn.execute('INSERT INTO reminders (title, due_time, completed, created_at) VALUES (?, ?, 0, ?)', (title, due, time.time()))
        conn.commit()
        return dict(conn.execute('SELECT * FROM reminders WHERE id = ?', (cursor.lastrowid,)).fetchone())
    finally:
        conn.close()


def claim_due_reminders():
    conn = get_connection()
    try:
        conn.execute('BEGIN IMMEDIATE')
        rows = conn.execute('SELECT * FROM reminders WHERE completed = 0 AND notified = 0 AND due_time <= ?', (time.time(),)).fetchall()
        conn.executemany('UPDATE reminders SET notified = 1 WHERE id = ?', [(r['id'],) for r in rows])
        conn.commit()
        return [dict(r) for r in rows]
    finally:
        conn.close()
