"""
audio/recorder.py
------------------
Handles ONLY audio recording. No AI logic lives here.
This mirrors the future ESP32 microphone module: later, this
file can be swapped for one that reads audio streamed over
Wi-Fi from the helmet's INMP441 microphone.
"""

import sounddevice as sd
from scipy.io.wavfile import write as wav_write

from config import SAMPLE_RATE, CHANNELS, VOICE_INPUT_PATH


def record(seconds: int, output_path: str = VOICE_INPUT_PATH) -> str:
    """
    Records audio from the default system microphone for a fixed duration.

    Args:
        seconds: how long to record, in seconds.
        output_path: where to save the resulting .wav file.

    Returns:
        The path to the saved recording.
    """
    print(f"[Recorder] Listening for {seconds} seconds...")

    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()  # Block until recording is finished

    wav_write(output_path, SAMPLE_RATE, audio)
    print(f"[Recorder] Saved recording to {output_path}")

    return output_path


def record_until_enter(output_path: str = VOICE_INPUT_PATH) -> str:
    """
    Alternative recording mode: starts recording immediately and
    stops when the user presses Enter. Useful when you don't want
    a fixed countdown.
    """
    import numpy as np

    print("[Recorder] Recording... press Enter to stop.")
    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16", callback=callback
    ):
        input()  # Waits for the user to press Enter

    audio = np.concatenate(frames, axis=0)
    wav_write(output_path, SAMPLE_RATE, audio)
    print(f"[Recorder] Saved recording to {output_path}")

    return output_path
