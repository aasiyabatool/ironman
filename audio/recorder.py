"""
audio/recorder.py
------------------
Handles ONLY audio recording. No AI logic lives here.
This mirrors the future ESP32 microphone module: later, this
file can be swapped for one that reads audio streamed over
Wi-Fi from the helmet's INMP441 microphone.
"""

import numpy as np
import sounddevice as sd
import webrtcvad
from scipy.io.wavfile import write as wav_write

from config import (
    SAMPLE_RATE,
    CHANNELS,
    VOICE_INPUT_PATH,
    VAD_AGGRESSIVENESS,
    VAD_FRAME_MS,
    VAD_SILENCE_SECONDS,
    VAD_MAX_RECORD_SECONDS,
    VAD_MIN_RECORD_SECONDS,
)


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


def record_vad(output_path: str = VOICE_INPUT_PATH) -> str:
    """
    Records audio from the default system microphone and stops
    automatically once VAD_SILENCE_SECONDS of continuous silence is
    detected after speech has started, instead of locking into a
    fixed-length window. Falls back to VAD_MAX_RECORD_SECONDS as a
    hard cap so a stuck/never-silent input can't record forever.

    webrtcvad requires 16-bit mono PCM at 8/16/32/48 kHz, in frames
    of exactly 10/20/30ms -- so we read the stream in small frames
    sized to VAD_FRAME_MS rather than one big fixed-duration block.

    Args:
        output_path: where to save the resulting .wav file.

    Returns:
        The path to the saved recording.
    """
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

    frame_samples = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)
    silence_frames_needed = int(VAD_SILENCE_SECONDS * 1000 / VAD_FRAME_MS)
    min_frames = int(VAD_MIN_RECORD_SECONDS * 1000 / VAD_FRAME_MS)
    max_frames = int(VAD_MAX_RECORD_SECONDS * 1000 / VAD_FRAME_MS)

    print("[Recorder] Listening (VAD auto-stop)...")

    frames = []
    speech_started = False
    consecutive_silence = 0

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16", blocksize=frame_samples
    ) as stream:
        for frame_count in range(max_frames):
            chunk, _ = stream.read(frame_samples)
            frames.append(chunk.copy())

            # webrtcvad only accepts single-channel frames.
            mono = chunk[:, 0] if chunk.ndim > 1 else chunk
            is_speech = vad.is_speech(mono.tobytes(), SAMPLE_RATE)

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
                print(f"[Recorder] Silence detected after {VAD_SILENCE_SECONDS}s -- stopping.")
                break
        else:
            print("[Recorder] Hit max recording length -- stopping.")

    audio = np.concatenate(frames, axis=0)
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
