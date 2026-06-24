"""
Real-time speech transcription using Faster Whisper.
Consumes audio chunks from AudioCapture and produces text segments.
"""

import queue
import threading
import numpy as np
from faster_whisper import WhisperModel

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class Transcriber:
    """
    Wraps Faster Whisper for real-time transcription.

    Usage:
        transcriber = Transcriber()
        transcriber.start()
        text = transcriber.get_text()   # blocking
        transcriber.stop()
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        model_size: tiny | base | small | medium
                    Start with 'base' — good balance of speed and accuracy.
                    Use 'small' or 'medium' for better accuracy (slower).
        device:     'cpu' for most laptops. 'cuda' if you have NVIDIA GPU.
        compute_type: 'int8' is fastest on CPU. 'float16' for GPU.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        self._text_queue: queue.Queue = queue.Queue()
        self._audio_queue: queue.Queue = queue.Queue()
        self._is_running = False
        self._worker_thread: threading.Thread | None = None
        self._model: WhisperModel | None = None

        logger.info(f"Transcriber created | model={model_size} | device={device}")

    def load_model(self) -> None:
        """
        Downloads and loads the Whisper model.
        First run will download the model (~150MB for base).
        Subsequent runs load from cache instantly.
        """
        logger.info(f"Loading Whisper model '{self.model_size}'... (first run downloads it)")
        print(f"Loading Whisper '{self.model_size}' model — please wait...")

        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )

        logger.info("Whisper model loaded successfully")
        print("Model loaded!")

    def transcribe_chunk(self, audio_chunk: np.ndarray) -> str:
        """
        Transcribe a single numpy audio chunk.
        Returns the transcribed text, or empty string if nothing detected.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Whisper expects float32 audio normalized between -1 and 1
        audio = audio_chunk.astype(np.float32)

        segments, info = self._model.transcribe(
            audio,
            beam_size=5,
            language="en",           # Force English — faster than auto-detect
            vad_filter=True,         # Skip silent parts automatically
            vad_parameters=dict(
                min_silence_duration_ms=300
            )
        )

        # Collect all segment texts
        text_parts = [segment.text.strip() for segment in segments]
        full_text = " ".join(text_parts).strip()

        if full_text:
            logger.debug(f"Transcribed: {full_text}")

        return full_text

    def _worker_loop(self) -> None:
        """
        Background thread: picks audio chunks from queue,
        transcribes them, puts text results in text queue.
        """
        logger.info("Transcriber worker thread started")

        while self._is_running:
            try:
                audio_chunk = self._audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                text = self.transcribe_chunk(audio_chunk)
                if text:
                    self._text_queue.put(text)
                    print(f"[Transcript] {text}")
            except Exception as e:
                logger.error(f"Transcription error: {e}")

        logger.info("Transcriber worker thread stopped")

    def start(self) -> None:
        """Load model and start background transcription worker."""
        if self._model is None:
            self.load_model()

        self._is_running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="TranscriberWorker"
        )
        self._worker_thread.start()
        logger.info("Transcriber started")

    def stop(self) -> None:
        """Stop the transcription worker."""
        self._is_running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=3.0)
        logger.info("Transcriber stopped")

    def feed_audio(self, audio_chunk: np.ndarray) -> None:
        """Feed an audio chunk into the transcription queue."""
        self._audio_queue.put(audio_chunk)

    def get_text(self, timeout: float = 5.0) -> str | None:
        """
        Get the next transcribed text from the output queue.
        Blocks until text is available or timeout reached.
        """
        try:
            return self._text_queue.get(timeout=timeout)
        except queue.Empty:
            return None