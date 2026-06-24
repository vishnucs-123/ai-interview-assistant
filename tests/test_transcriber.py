"""
Test Phase 2: Audio capture + transcription pipeline.
Run: python -m tests.test_transcriber
Speak clearly into your mic for 10 seconds.
"""

import time
from backend.audio.audio_capture import AudioCapture
from backend.transcriber.transcriber import Transcriber


def test_transcriber():
    print("=== Phase 2: Transcription Test ===\n")

    transcriber = Transcriber(model_size="base", device="cpu", compute_type="int8")
    transcriber.start()

    capture = AudioCapture()
    capture.start()

    print("Speak into your mic for 10 seconds...\n")

    start = time.time()
    while time.time() - start < 10.0:
        chunk = capture.get_chunk(timeout=1.0)
        if chunk is not None:
            transcriber.feed_audio(chunk)

    capture.stop()
    transcriber.stop()

    print("\n=== Test complete ===")


if __name__ == "__main__":
    test_transcriber()