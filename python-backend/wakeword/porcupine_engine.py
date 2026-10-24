import os
import pvporcupine
import sounddevice as sd
import numpy as np
import threading
from typing import Optional, Callable, Tuple

class PorcupineWakeWordEngine:
    def __init__(self):
        self._porcupine = None
        self._is_listening = False
        self._thread: Optional[threading.Thread] = None
        self._on_wake_detected: Optional[Callable[[], None]] = None
        self._access_key: str = ""
        self._keyword_path: Optional[str] = None
        self._sensitivity: float = 0.5
        self._status: str = "UNINITIALIZED" # UNINITIALIZED, SETUP_REQUIRED, READY, LISTENING, ERROR
        self._error_message: str = ""

    @property
    def status(self) -> str:
        return self._status

    @property
    def error_message(self) -> str:
        return self._error_message

    def configure(self, access_key: str, keyword_path: Optional[str] = None, sensitivity: float = 0.5) -> Tuple[bool, str]:
        self.stop_listening()
        self._access_key = access_key.strip()
        self._keyword_path = keyword_path.strip() if keyword_path else None
        self._sensitivity = max(0.0, min(1.0, sensitivity))

        if not self._access_key:
            self._status = "SETUP_REQUIRED"
            self._error_message = "Picovoice AccessKey is required for wake word detection."
            return False, self._error_message

        try:
            if self._porcupine:
                self._porcupine.delete()
                self._porcupine = None

            if self._keyword_path and os.path.exists(self._keyword_path):
                self._porcupine = pvporcupine.create(
                    access_key=self._access_key,
                    keyword_paths=[self._keyword_path],
                    sensitivities=[self._sensitivity]
                )
            else:
                self._status = "SETUP_REQUIRED"
                self._error_message = 'Select a valid custom "Hey Oska" .ppn keyword model.'
                return False, self._error_message

            self._status = "READY"
            self._error_message = ""
            return True, "Wake word engine initialized successfully."
        except Exception as e:
            self._status = "ERROR"
            self._error_message = str(e)
            print(f"[WakeWord] Porcupine init error: {e}")
            return False, str(e)

    def start_listening(self, callback: Callable[[], None], device_index: Optional[int] = None) -> bool:
        if self._is_listening:
            return True
        if not self._porcupine or self._status != "READY":
            print(f"[WakeWord] Cannot start: engine status is {self._status}")
            return False

        if self._is_listening:
            return True

        self._on_wake_detected = callback
        self._is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, args=(device_index,), daemon=True)
        self._thread.start()
        self._status = "LISTENING"
        return True

    def stop_listening(self):
        self._is_listening = False
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)
        self._thread = None
        if self._status == "LISTENING":
            self._status = "READY"

    def _listen_loop(self, device_index: Optional[int]):
        try:
            with sd.InputStream(
                samplerate=self._porcupine.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=self._porcupine.frame_length,
                device=device_index
            ) as stream:
                while self._is_listening:
                    pcm, overflow = stream.read(self._porcupine.frame_length)
                    if overflow:
                        pass
                    keyword_index = self._porcupine.process(pcm.flatten())
                    if keyword_index >= 0:
                        print("[WakeWord] 'Hey Oska' / wake keyword detected!")
                        if self._on_wake_detected:
                            try:
                                self._on_wake_detected()
                            except Exception as ex:
                                print(f"[WakeWord] Callback error: {ex}")
                        # Sleep briefly to prevent duplicate detections
                        threading.Event().wait(1.5)
        except Exception as e:
            print(f"[WakeWord] Audio loop error: {e}")
            self._status = "ERROR"
            self._error_message = str(e)
        finally:
            self._is_listening = False

    def close(self):
        self.stop_listening()
        if self._porcupine:
            try:
                self._porcupine.delete()
            except Exception:
                pass
            self._porcupine = None
