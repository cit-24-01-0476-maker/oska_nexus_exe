import sounddevice as sd
import numpy as np
import threading
import time
from voice.activity import VoiceActivity
from typing import List, Dict, Optional, Callable, Any

class AudioCapture:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._is_recording = False
        self._audio_buffer: List[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: Optional[sd.InputStream] = None
        self._device_index: Optional[int] = None
        self._on_waveform: Optional[Callable[[float], None]] = None
        self._activity = VoiceActivity(time.monotonic())

    @staticmethod
    def list_input_devices() -> List[Dict[str, Any]]:
        devices = sd.query_devices()
        input_devs = []
        for i, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                input_devs.append({
                    "id": i,
                    "name": dev.get('name'),
                    "channels": dev.get('max_input_channels'),
                    "default": i == sd.default.device[0]
                })
        return input_devs

    def set_device(self, device_id: Optional[int]):
        if self._device_index != device_id:
            self.close()
        self._device_index = device_id

    def set_waveform_callback(self, callback: Optional[Callable[[float], None]]):
        self._on_waveform = callback

    def _audio_callback(self, indata, frames, time_info, status):
        rms = float(np.sqrt(np.mean(indata**2)))
        if status:
            pass
        if self._is_recording:
            with self._lock:
                self._audio_buffer.append(indata.copy())
                self._activity.feed(rms, frames / self.sample_rate, time.monotonic())

        # Compute RMS energy for real-time visual reactive waveform
        normalized_rms = min(1.0, float(rms * 12.0))
        if self._on_waveform:
            try:
                self._on_waveform(normalized_rms)
            except Exception:
                pass

    def start_recording(self):
        with self._lock:
            self._audio_buffer = []
            self._is_recording = True
            self._activity = VoiceActivity(time.monotonic())

        if self._stream is None:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=self._device_index,
                blocksize=1024,
                callback=self._audio_callback
            )
            self._stream.start()

    def wait_for_utterance(self, shutdown, cancelled):
        while not shutdown.is_set() and not cancelled.is_set():
            with self._lock:
                if self._activity.finished(time.monotonic()):
                    return self._activity.has_speech
            cancelled.wait(0.05)
        return False

    def stop_recording(self) -> np.ndarray:
        self.close()
        with self._lock:
            self._is_recording = False
            if self._audio_buffer:
                concatenated = np.concatenate(self._audio_buffer, axis=0)
                self._audio_buffer = []
                return concatenated.flatten()
            return np.array([], dtype='float32')

    def close(self):
        self._is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
