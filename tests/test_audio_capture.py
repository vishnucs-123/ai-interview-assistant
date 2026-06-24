import time
from backend.audio.audio_capture import AudioCapture

def test_capture():
    print("Available audio devices:")
    capture = AudioCapture()
    capture.list_devices()

    print("\nStarting 5-second capture test...")
    print("Speak into your microphone now!\n")

    chunk_count = 0

    with AudioCapture() as cap:
        start = time.time()
        while time.time() - start < 5.0:
            chunk = cap.get_chunk(timeout=1.0)
            if chunk is not None:
                chunk_count += 1
                print(f"  Chunk {chunk_count}: {len(chunk)} samples | RMS: {(chunk**2).mean()**0.5:.4f}")

    print(f"\nTest complete. Received {chunk_count} audio chunks.")
    print("Check logs/app.log for detailed logs.")

if __name__ == "__main__":
    test_capture()