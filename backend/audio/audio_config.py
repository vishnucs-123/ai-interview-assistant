"""
Audio capture configuration.
Centralizes all tunable audio settings in one place.
"""

from dataclasses import dataclass


@dataclass
class AudioConfig:
    """
    All audio capture parameters.
    Modify here — don't hardcode values in capture logic.
    """

    # Sample rate: 16000 Hz is ideal for Whisper (speech recognition)
    sample_rate: int = 16000

    # Mono (1 channel) is sufficient for speech and expected by Whisper
    channels: int = 1

    # Audio chunk size in seconds — sent to transcriber every N seconds
    chunk_duration_seconds: float = 1.0

    # dtype for audio samples
    dtype: str = "float32"

    # Buffer size: samples per chunk = sample_rate * chunk_duration
    @property
    def chunk_size(self) -> int:
        return int(self.sample_rate * self.chunk_duration_seconds)

    # Silence threshold — audio below this RMS level is considered silence
    silence_threshold: float = 0.01

    # Max silence duration before auto-stopping a segment (seconds)
    max_silence_duration: float = 2.0


# Singleton config instance used across the app
DEFAULT_AUDIO_CONFIG = AudioConfig()