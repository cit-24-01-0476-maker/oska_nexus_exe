import threading
import time
from enum import Enum
from typing import Callable, List, Optional, Dict, Any

class AssistantState(str, Enum):
    STOPPED = "STOPPED"
    IDLE = "IDLE"
    WAKE_LISTENING = "WAKE_LISTENING"
    WAKE_DETECTED = "WAKE_DETECTED"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

class StateMachine:
    def __init__(self, initial_state: AssistantState = AssistantState.IDLE):
        self._state: AssistantState = initial_state
        self._lock = threading.Lock()
        self._listeners: List[Callable[[AssistantState, Optional[Dict[str, Any]]], None]] = []
        self._context: Dict[str, Any] = {
            "last_error": None,
            "transcript": "",
            "response": "",
            "pending_confirmation": None,
            "waveform_level": 0.0,
            "timestamp": time.time()
        }

    @property
    def current_state(self) -> AssistantState:
        with self._lock:
            return self._state

    @property
    def context(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._context)

    def subscribe(self, callback: Callable[[AssistantState, Optional[Dict[str, Any]]], None]):
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[AssistantState, Optional[Dict[str, Any]]], None]):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def transition_to(self, new_state: AssistantState, metadata: Optional[Dict[str, Any]] = None):
        with self._lock:
            old_state = self._state
            self._state = new_state
            self._context["timestamp"] = time.time()
            if metadata:
                self._context.update(metadata)
            listeners_copy = list(self._listeners)
            context_copy = dict(self._context)

        # Notify outside lock to prevent deadlocks
        for listener in listeners_copy:
            try:
                listener(new_state, context_copy)
            except Exception as e:
                print(f"[StateMachine] Listener error: {e}")

    def update_context(self, updates: Dict[str, Any]):
        with self._lock:
            self._context.update(updates)
            listeners_copy = list(self._listeners)
            context_copy = dict(self._context)
            current_st = self._state

        for listener in listeners_copy:
            try:
                listener(current_st, context_copy)
            except Exception:
                pass
