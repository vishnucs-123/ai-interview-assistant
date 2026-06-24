"""
Real-time audio capture module.
Captures microphone audio in chunks and puts them in a queue
for the transcriber to consume.

Phase 1 — Microphone only.
System audio (loopback) will be added in Phase 2.
"""

import queue
import threading
import numpy as np
import sounddevice as sd

from backend.audio.audio_config import AudioConfig, DEFAULT_AUDIO_CONFIG
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AudioCapture:
    """
    Captures microphone audio in real time.
    
    Usage:
        capture = AudioCapture()
        capture.start()
        chunk = capture.get_chunk()   # blocking, returns numpy array
        capture.stop()
    """

    def __init__(self, config: AudioConfig = DEFAULT_AUDIO_CONFIG):
        self.config = config
        self._audio_queue: queue.Queue = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._is_running: bool = False
        self._lock = threading.Lock()

        logger.info(
            f"AudioCapture initialized | "
            f"sample_rate={config.sample_rate} | "
            f"channels={config.channels} | "
            f"chunk_duration={config.chunk_duration_seconds}s"
        )

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time,
        status
    ) -> None:
        """
        Called by sounddevice on every audio chunk.
        Runs in a separate thread — keep it fast, no blocking I/O here.
        """
        if status:
            logger.warning(f"Audio callback status: {status}")

        # Copy to avoid mutation after callback returns
        chunk = indata.copy().flatten()

        # Skip silent chunks to reduce load on transcriber
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        if rms < self.config.silence_threshold:
            return

        self._audio_queue.put(chunk)

    def start(self) -> None:
        """Start capturing audio from the default microphone."""
        with self._lock:
            if self._is_running:
                logger.warning("AudioCapture already running — ignoring start()")
                return

            logger.info("Starting audio capture...")

            self._stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=self.config.dtype,
                blocksize=self.config.chunk_size,
                callback=self._audio_callback
            )
            self._stream.start()
            self._is_running = True
            logger.info("Audio capture started successfully")

    def stop(self) -> None:
        """Stop capturing audio and release the stream."""
        with self._lock:
            if not self._is_running:
                return

            logger.info("Stopping audio capture...")

            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            self._is_running = False
            logger.info("Audio capture stopped")

    def get_chunk(self, timeout: float = 5.0) -> np.ndarray | None:
        """
        Get the next audio chunk from the queue.
        Blocks until a chunk is available or timeout is reached.
        
        Returns:
            numpy array of audio samples, or None on timeout
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            logger.debug("get_chunk() timed out — no audio in queue")
            return None

    def is_running(self) -> bool:
        return self._is_running

    def clear_queue(self) -> None:
        """Flush all buffered audio chunks."""
        cleared = 0
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
                cleared += 1
            except queue.Empty:
                break
        logger.debug(f"Cleared {cleared} chunks from audio queue")

    def list_devices(self) -> None:
        """Print all available audio devices — useful for debugging."""
        print(sd.query_devices())

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()