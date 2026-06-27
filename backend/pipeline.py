import threading
import queue
from PyQt6.QtCore import QObject, pyqtSignal

from backend.audio.audio_capture import AudioCapture
from backend.transcriber.transcriber import Transcriber
from backend.transcriber.question_detector import QuestionDetector
from backend.llm.answer_engine import AnswerEngine
from backend.memory.conversation_memory import ConversationMemory
from backend.memory.memory_store import MemoryStore
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class Pipeline(QObject):
    """
    Orchestrates the full real-time pipeline.
    Emits Qt signals so the overlay UI updates safely from any thread.
    """

    # Signals — connected to overlay window
    answer_ready = pyqtSignal(str, str, str)   # question, answer, category
    transcript_update = pyqtSignal(str)         # transcript text
    status_update = pyqtSignal(str)             # status message

    def __init__(
        self,
        whisper_model: str = "base",
        ollama_model: str = "llama3.2"
    ):
        super().__init__()

        self._is_running = False
        self._is_muted = False

        # Components
        self._capture = AudioCapture()
        self._transcriber = Transcriber(model_size=whisper_model)
        self._detector = QuestionDetector()
        self._engine = AnswerEngine(model=ollama_model)

        # Memory
        self._memory = ConversationMemory(max_entries=20)
        self._store = MemoryStore()
        self._session_id = self._store.new_session()

        # Internal queue between transcriber output and detector/engine
        self._text_queue: queue.Queue = queue.Queue()

        # Background threads
        self._capture_thread: threading.Thread | None = None
        self._answer_thread: threading.Thread | None = None

        logger.info("Pipeline initialized")

    def start(self) -> None:
        """Start the full pipeline."""
        logger.info("Starting pipeline...")
        self.status_update.emit("Loading Whisper model...")

        # Load transcriber model (blocking — done before threads start)
        self._transcriber.load_model()

        self._is_running = True

        # Thread 1: Audio capture → transcription
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name="CaptureLoop"
        )
        self._capture_thread.start()

        # Thread 2: Text → detection → answer generation
        self._answer_thread = threading.Thread(
            target=self._answer_loop,
            daemon=True,
            name="AnswerLoop"
        )
        self._answer_thread.start()

        self.status_update.emit("Listening...")
        logger.info("Pipeline running")

    def stop(self) -> None:
        """Stop all pipeline components."""
        self._is_running = False
        self._capture.stop()
        self._transcriber.stop()
        self._store.end_session(
            self._session_id,
            summary=str(self._memory.get_summary())
        )
        self._store.close()
        logger.info("Pipeline stopped")

    def set_muted(self, muted: bool) -> None:
        self._is_muted = muted
        logger.info(f"Pipeline muted={muted}")

    def get_memory_summary(self) -> dict:
        """Return current session summary — used by analytics."""
        return self._memory.get_summary()

    # ------------------------------------------------------------------ #
    # Background loops
    # ------------------------------------------------------------------ #

    def _capture_loop(self) -> None:
        """
        Thread 1: Captures audio → transcribes → puts text in queue.
        """
        logger.info("Capture loop started")
        self._capture.start()
        self._transcriber.start()

        while self._is_running:
            if self._is_muted:
                import time
                time.sleep(0.1)
                continue

            # Get audio chunk from mic
            chunk = self._capture.get_chunk(timeout=1.0)
            if chunk is None:
                continue

            # Feed to transcriber
            self._transcriber.feed_audio(chunk)

            # Get transcribed text
            text = self._transcriber.get_text(timeout=0.5)
            if text:
                logger.debug(f"Transcript: {text}")
                self.transcript_update.emit(text)
                self._text_queue.put(text)

        self._capture.stop()
        logger.info("Capture loop stopped")

    def _answer_loop(self) -> None:
        """
        Thread 2: Reads transcribed text → detects question → generates answer.
        """
        logger.info("Answer loop started")

        while self._is_running:
            try:
                text = self._text_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # Detect if it's a question
            detected = self._detector.detect(text)

            if not detected.is_question or detected.confidence < 0.5:
                logger.debug(f"Skipped (not a question): {text}")
                continue

            logger.info(
                f"Question detected: {detected.category} | {detected.topic}"
            )
            self.status_update.emit("Generating answer...")

            # Build prompt with memory context for better answers
            context = self._memory.get_context(last_n=5)
            if context:
                detected.text = f"{detected.text}\n\n{context}"

            # Generate answer
            answer = self._engine.generate(detected)

            # Save to memory
            self._memory.add(
                text,                  # original question without context
                answer.answer,
                detected.category,
                detected.topic
            )
            self._store.save_exchange(
                self._session_id,
                text,
                answer.answer,
                detected.category,
                detected.topic
            )

            # Emit to UI (safe cross-thread signal)
            self.answer_ready.emit(
                text,
                answer.answer,
                detected.category
            )
            self.status_update.emit("Listening...")

        logger.info("Answer loop stopped")
