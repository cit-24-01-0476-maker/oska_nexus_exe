"""Deterministic voice endpoint detection, sensitive to all standard microphones."""
class VoiceActivity:
    def __init__(self, started_at, threshold=0.0015):
        self.started_at = started_at
        self.threshold = threshold
        self.voiced_seconds = 0.0
        self.last_voice_at = None

    def feed(self, rms, duration, now):
        if rms >= self.threshold:
            self.voiced_seconds += duration
            self.last_voice_at = now

    @property
    def has_speech(self):
        return self.voiced_seconds >= 0.08

    def finished(self, now, silence_seconds=1.0, no_speech_seconds=8.0, max_seconds=15.0):
        if now - self.started_at >= max_seconds:
            return True
        if self.has_speech:
            return (now - self.last_voice_at) >= silence_seconds if self.last_voice_at else False
        return (now - self.started_at) >= no_speech_seconds
