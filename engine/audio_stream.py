"""
engine/audio_stream.py
--------------------------
Owns the ONE continuous microphone stream for the whole assistant.
(See earlier version's docstring for the full architecture explanation
-- this version adds status LED updates at the key state transitions.)
"""

import os
import time
from collections import deque

import numpy as np
import onnxruntime as ort
import openwakeword
from openwakeword.model import Model
import sounddevice as sd
import webrtcvad
from scipy.io.wavfile import write as wav_write

# See wakeword/listener.py for why this is set before the model loads --
# suppresses noisy GPU auto-discovery warnings from the ONNX backend on
# the Pi (e.g. "Failed to detect devices under /sys/class/drm/card0"),
# which are harmless since it falls back to CPU anyway.
ort.set_default_logger_severity(3)

from config import (
    WAKE_WORD_THRESHOLD,
    WAKE_WORD_THRESHOLD_WHILE_SPEAKING,
    RECORD_SECONDS,
    RECORDINGS_DIR,
    USE_VAD_CAPTURE,
    VAD_AGGRESSIVENESS,
    VAD_FRAME_MS,
    VAD_SILENCE_SECONDS,
    VAD_MIN_RECORD_SECONDS,
    VAD_MAX_RECORD_SECONDS,
    AUTH_CLIP_SECONDS,
)
from engine.state import SharedState
from commands.status_led import set_status

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # ~80ms per chunk, the size openWakeWord expects
WARMUP_CHUNKS = 19  # ~1.5s, flushes stale buffers

# How many CHUNK_SIZE chunks make up the rolling auth buffer -- e.g.
# 2.0s / 80ms ~= 25 chunks. This buffer is what gets snapshotted for
# voice authentication the instant "Hey Jarvis" fires, so it holds
# the wake-word phrase itself rather than anything said afterward.
AUTH_CLIP_CHUNKS = max(1, int((SAMPLE_RATE * AUTH_CLIP_SECONDS) / CHUNK_SIZE))


def _load_model() -> Model:
    print("[AudioStream] Loading wake word model (first run downloads it)...")
    openwakeword.utils.download_models()
    return Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")


_vad = webrtcvad.Vad(VAD_AGGRESSIVENESS) if USE_VAD_CAPTURE else None
VAD_FRAME_SAMPLES = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)


def _capture_command_fixed(stream) -> str:
    """
    Records RECORD_SECONDS of audio directly from the already-open
    stream and saves it to a uniquely named .wav file.
    """
    total_chunks = max(1, int((SAMPLE_RATE * RECORD_SECONDS) / CHUNK_SIZE))
    frames = []

    print(f"[AudioStream] Recording your command ({RECORD_SECONDS}s)...")
    for _ in range(total_chunks):
        chunk, _ = stream.read(CHUNK_SIZE)
        frames.append(chunk.copy())

    return _save_command(frames)


def _capture_command_vad(stream) -> str:
    """
    Records from the already-open stream and stops automatically once
    VAD_SILENCE_SECONDS of continuous silence follows detected speech,
    instead of always recording a rigid RECORD_SECONDS window. This
    cuts latency on short commands and avoids truncating longer ones.

    Reads in small VAD_FRAME_MS frames (webrtcvad only accepts 10/20/30ms
    frames), independent of the wake-word engine's CHUNK_SIZE.
    """
    silence_frames_needed = int(VAD_SILENCE_SECONDS * 1000 / VAD_FRAME_MS)
    min_frames = int(VAD_MIN_RECORD_SECONDS * 1000 / VAD_FRAME_MS)
    max_frames = int(VAD_MAX_RECORD_SECONDS * 1000 / VAD_FRAME_MS)

    print("[AudioStream] Recording your command (auto-stop on silence)...")

    frames = []
    speech_started = False
    consecutive_silence = 0

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
            print(f"[AudioStream] Silence detected after {VAD_SILENCE_SECONDS}s -- stopping.")
            break
    else:
        print("[AudioStream] Hit max recording length -- stopping.")

    return _save_command(frames)


def _save_command(frames) -> str:
    audio = np.concatenate(frames, axis=0)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(RECORDINGS_DIR, f"command_{timestamp}.wav")
    wav_write(path, SAMPLE_RATE, audio)
    return path


def _capture_command(stream) -> str:
    """Captures one voice command, using VAD auto-stop when enabled."""
    if USE_VAD_CAPTURE:
        return _capture_command_vad(stream)
    return _capture_command_fixed(stream)


def _save_auth_clip(rolling_buffer: "deque") -> str:
    """
    Snapshots the rolling buffer (the last AUTH_CLIP_SECONDS of raw
    audio, which already contains the "Hey Jarvis" phrase that just
    triggered detection) and saves it as the auth clip. No extra
    speech is recorded -- the wake word IS the auth sample.
    """
    frames = list(rolling_buffer)
    audio = np.concatenate(frames, axis=0)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(RECORDINGS_DIR, f"auth_{timestamp}.wav")
    wav_write(path, SAMPLE_RATE, audio)
    return path


def run(state: SharedState) -> None:
    """
    The background thread's main loop. Runs until
    state.shutdown_requested is set.
    """
    model = _load_model()

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE
    ) as stream:
        print("[AudioStream] Warming up (give it a second before saying 'Hey Jarvis')...")
        for _ in range(WARMUP_CHUNKS):
            warm_chunk, _ = stream.read(CHUNK_SIZE)
            model.predict(warm_chunk.flatten())

        print("[AudioStream] Listening for 'Hey Jarvis'...")
        set_status("ready")  # idle, waiting for the wake word

        # Rolling buffer of the last AUTH_CLIP_SECONDS of raw audio.
        # Continuously overwritten chunk by chunk so that whenever the
        # wake word fires, it already holds the "Hey Jarvis" phrase
        # itself -- this is what auth mode snapshots, instead of
        # recording anything the user says afterward.
        rolling_buffer = deque(maxlen=AUTH_CLIP_CHUNKS)

        while not state.shutdown_requested.is_set():
            chunk, _ = stream.read(CHUNK_SIZE)
            rolling_buffer.append(chunk.copy())

            predictions = model.predict(chunk.flatten())

            active_threshold = (
                WAKE_WORD_THRESHOLD_WHILE_SPEAKING
                if state.is_speaking.is_set()
                else WAKE_WORD_THRESHOLD
            )

            detected = any(score > active_threshold for score in predictions.values())

            if detected:
                print("[AudioStream] Wake word detected!")
                model.reset()

                state.interrupt_requested.set()

                if state.auth_mode.is_set():
                    # Voice-auth stage: the wake word IS the sample.
                    # Snapshot the rolling buffer right now -- do NOT
                    # record anything further -- and hand it off for
                    # speaker verification.
                    set_status("processing")
                    print("[AudioStream] Capturing 'Hey Jarvis' for voice authentication...")
                    auth_clip_path = _save_auth_clip(rolling_buffer)

                    while not state.auth_queue.empty():
                        try:
                            state.auth_queue.get_nowait()
                        except Exception:
                            break

                    state.auth_queue.put(auth_clip_path)

                else:
                    set_status("listening")  # wake word heard, now recording

                    command_path = _capture_command(stream)

                    # Drop any stale queued command(s) so JARVIS always
                    # responds to what you just said, not a growing
                    # backlog from earlier in the conversation.
                    while not state.command_queue.empty():
                        try:
                            state.command_queue.get_nowait()
                        except Exception:
                            break

                    state.command_queue.put(command_path)
                    queue_depth = state.command_queue.qsize()
                    if queue_depth > 0:
                        print(f"[AudioStream] Command queued ({queue_depth} pending) -- JARVIS is still catching up.")

                for _ in range(WARMUP_CHUNKS):
                    warm_chunk, _ = stream.read(CHUNK_SIZE)
                    rolling_buffer.append(warm_chunk.copy())
                    model.predict(warm_chunk.flatten())

                print("[AudioStream] Listening for 'Hey Jarvis'...")
                # Note: status goes to "processing" once main.py picks up
                # the command, and back to "ready" once it finishes --
                # see the set_status() calls in main.py's run_once().
