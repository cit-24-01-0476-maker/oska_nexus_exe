import os
import re
import numpy as np
import threading
from typing import Optional, Tuple
from assistant.text_io import safe_print as print

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class FasterWhisperSTT:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._lock = threading.Lock()
        self._is_loading = False
        self._sr_recognizer = sr.Recognizer() if SR_AVAILABLE else None
        if self._sr_recognizer:
            self._sr_recognizer.operation_timeout = 8

    def load_model(self) -> Tuple[bool, str]:
        with self._lock:
            if self._model is not None:
                return True, "Model already loaded"
            self._is_loading = True

        try:
            from faster_whisper import WhisperModel
            print(f"[STT] Loading Faster-Whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
            model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            with self._lock:
                self._model = model
                self._is_loading = False
            print("[STT] Faster-Whisper model loaded successfully.")
            return True, "Loaded"
        except Exception as e:
            with self._lock:
                self._is_loading = False
            print(f"[STT] Error loading Faster-Whisper model: {e}")
            return False, str(e)

    def _transcribe_google(self, audio_data: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        if not SR_AVAILABLE or self._sr_recognizer is None:
            return None
        try:
            # Convert float32 [-1.0, 1.0] to 16-bit PCM
            clipped = np.clip(audio_data, -1.0, 1.0)
            pcm16 = (clipped * 32767.0).astype(np.int16).tobytes()
            sr_audio = sr.AudioData(pcm16, 16000, 2)

            # Try 1: Sinhala (si-LK)
            try:
                text_si = self._sr_recognizer.recognize_google(sr_audio, language="en-US" if language == "en" else "si-LK")
                if text_si and text_si.strip():
                    return text_si.strip()
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"[STT Google si-LK error]: {e}")

            # Try 2: English (en-US / en-IN)
            try:
                text_en = self._sr_recognizer.recognize_google(sr_audio, language="en-US")
                if text_en and text_en.strip():
                    return text_en.strip()
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"[STT Google en-US error]: {e}")

        except Exception as e:
            print(f"[STT Google recognition general error]: {e}")
        return None

    def _clean_hallucinations(self, text: str) -> str:
        """
        Filters out CJK characters (Chinese, Japanese, Korean) or Arabic that
        Whisper hallucinates on non-English/Sinhala ambient room audio.
        """
        # If text consists of CJK or Arabic characters, reject it
        if re.search(r'[\u4e00-\u9fff\u3040-\u30ff\u0600-\u06ff]', text):
            return ""
        return text.strip()

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> str:
        if audio_data is None or len(audio_data) == 0:
            return ""

        # Step 1: High accuracy online recognition (Native Sinhala si-LK & English)
        google_result = self._transcribe_google(audio_data, language)
        if google_result:
            print(f"[STT Engine: Google Online] Recognized: '{google_result}'")
            return google_result

        # Step 2: Offline Faster-Whisper fallback
        if self._model is None:
            success, err = self.load_model()
            if not success:
                return ""

        try:
            prompt = "Sinhala, English, සිංහල, Oska Nexus, welawa, chrome, volume, youtube"
            segments, info = self._model.transcribe(
                audio_data,
                beam_size=3,
                language=language,
                initial_prompt=prompt,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )

            text_chunks = [segment.text for segment in segments]
            full_text = " ".join(text_chunks).strip()
            cleaned = self._clean_hallucinations(full_text)
            print(f"[STT Engine: Faster-Whisper] Recognized: '{cleaned}' (Detected lang: {info.language})")
            return cleaned
        except Exception as e:
            print(f"[STT] Whisper Transcription error: {e}")
            return ""
