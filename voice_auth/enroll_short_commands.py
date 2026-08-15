"""
voice_auth/enroll_short_commands.py
------------------------------------
Supplemental enrollment: records SHORT command-length clips (using
the same VAD auto-stop behavior as the live pipeline) and adds them
to an existing enrolled person's folder.

Why this exists: the original enrollment samples were long (3s)
continuous speech, but real commands are short ("turn on the
lights"). Resemblyzer embeddings get noisier on short utterances, so
a voiceprint built only from long clips doesn't represent what your
voice's embedding looks like at real command length -- causing
lower similarity on genuine short commands. Adding short samples
into the same person's folder and rebuilding the voiceprint closes
that gap.

Usage:
    python -m voice_auth.enroll_short_commands aasiya
"""

import os
import sys
import time

import numpy as np
import sounddevice as sd
import webrtcvad
from scipy.io.wavfile import write as wav_write

from voice_auth.config import TRAINING_DATA_DIR

SAMPLE_RATE = 16000
VAD_FRAME_MS = 20
VAD_FRAME_SAMPLES = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)
VAD_AGGRESSIVENESS = 2
VAD_SILENCE_SECONDS = 1.0
VAD_MIN_RECORD_SECONDS = 0.4
VAD_MAX_RECORD_SECONDS = 5.0

_vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)


def _record_one() -> np.ndarray:
    silence_frames_needed = int(VAD_SILENCE_SECONDS * 1000 / VAD_FRAME_MS)
    min_frames = int(VAD_MIN_RECORD_SECONDS * 1000 / VAD_FRAME_MS)
    max_frames = int(VAD_MAX_RECORD_SECONDS * 1000 / VAD_FRAME_MS)

    frames = []
    speech_started = False
    consecutive_silence = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        for frame_count in range(max_frames):
            chunk, _ = stream.read(VAD_FRAME_SAMPLES)
            frames.append(chunk.copy())

            mono = chunk[:, 0] if chunk.ndim > 1 else chunk
            is_speech = _vad.is_speech(mono.tobytes(), SAMPLE_RATE)

            if is_speech:
                speech_started = True
                consecutive_silence = 0
            elif speech_started:
                consecutive_silence += 1

            if (
                speech_started
                and frame_count >= min_frames
                and consecutive_silence >= silence_frames_needed
            ):
                break

    return np.concatenate(frames, axis=0)


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m voice_auth.enroll_short_commands <name>")
        sys.exit(1)

    name = sys.argv[1]
    person_dir = os.path.join(TRAINING_DATA_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    print(f"[EnrollShort] Adding short-command samples for '{name}'.")
    print("Say short, natural commands like you actually would to JARVIS")
    print("(e.g. 'turn on the lights', 'activate combat mode', 'what's the status').")
    print("Aim for 15-20 samples covering a mix of your real commands.")
    print("Press Ctrl+C when done.\n")

    count = 0
    try:
        while True:
            input("Press Enter, then speak a short command...")
            audio = _record_one()
            count += 1
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            path = os.path.join(person_dir, f"short_{timestamp}_{count}.wav")
            wav_write(path, SAMPLE_RATE, audio)
            print(f"  Saved ({len(audio) / SAMPLE_RATE:.2f}s) -> {path}\n")
    except KeyboardInterrupt:
        print(f"\n[EnrollShort] Done. Added {count} short-command samples for '{name}'.")
        print("Next: rebuild voiceprints with 'python -m voice_auth.build_voiceprints'")


if __name__ == "__main__":
    main()
