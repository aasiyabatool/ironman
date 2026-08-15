"""
voice_auth/live_test.py
---------------------------
Records a short clip from your microphone and identifies who's
speaking (or reports "unknown"). Test with multiple enrolled people
and a few strangers to see how well it distinguishes everyone.

Usage:
    python -m voice_auth.live_test
"""

import os

import sounddevice as sd
from scipy.io.wavfile import write as wav_write

from voice_auth.config import SAMPLE_RATE, RECORD_SECONDS, TRAINING_DATA_DIR
from voice_auth.verify import is_authorized

TEST_CLIP_PATH = os.path.join(TRAINING_DATA_DIR, "_live_test_clip.wav")


def record_test_clip() -> str:
    print(f"\nSpeak now ({RECORD_SECONDS} seconds)...")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    wav_write(TEST_CLIP_PATH, SAMPLE_RATE, audio)
    return TEST_CLIP_PATH


if __name__ == "__main__":
    print("Voice Authentication Live Test")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            input("Press Enter, then speak...")
            clip_path = record_test_clip()

            authorized, name, confidence = is_authorized(clip_path)

            if authorized:
                print(f"AUTHORIZED: {name} (confidence: {confidence:.1%})\n")
            else:
                print(f"NOT AUTHORIZED (closest match: {name}, confidence: {confidence:.1%})\n")

    except KeyboardInterrupt:
        print("\nStopped.")
