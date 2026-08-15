"""
voice_auth/enroll.py
------------------------
Records voice samples for a NAMED person. Run this once per
authorized person you want the model to recognize, and once for
"unknown" if you want to add real (non-synthetic) non-authorized
voice samples on top of the ones generate_synthetic_negatives.py
creates.

Usage:
    python -m voice_auth.enroll
    Enter the person's name: aasiya
    (repeat later with a different name for a second person)
"""

import os
import time

import sounddevice as sd
from scipy.io.wavfile import write as wav_write

from voice_auth.config import SAMPLE_RATE, RECORD_SECONDS, TRAINING_DATA_DIR


def record_sample(output_dir: str, index: int) -> str:
    print(f"\nRecording sample {index}... speak now (any phrase, {RECORD_SECONDS}s)")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(output_dir, f"sample_{timestamp}_{index}.wav")
    wav_write(path, SAMPLE_RATE, audio)
    print(f"Saved: {path}")
    return path


def enroll_batch(name: str, count: int) -> None:
    person_dir = os.path.join(TRAINING_DATA_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    existing_count = len(
        [f for f in os.listdir(person_dir) if f.lower().endswith((".wav", ".mp3"))]
    )

    print(f"\nRecording {count} samples for '{name}' into {person_dir}")
    print("Vary your phrases and tone a bit between recordings for better accuracy.\n")

    for i in range(1, count + 1):
        input(f"Press Enter, then speak for sample {i}/{count}...")
        record_sample(person_dir, existing_count + i)

    print(f"\nDone. Samples saved to {person_dir}")


if __name__ == "__main__":
    print("Voice Authentication Enrollment")
    print("Enter a person's name to enroll them, or 'unknown' to add real")
    print("non-authorized voice samples (in addition to the synthetic ones).\n")

    name = input("Person's name: ").strip().lower().replace(" ", "_")

    if not name:
        print("No name entered, exiting.")
    else:
        count_input = input("How many samples to record? (recommended: 20-30): ").strip()
        count = int(count_input) if count_input else 20
        enroll_batch(name, count)
