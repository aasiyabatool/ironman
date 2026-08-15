"""
wakeword/listener.py
------------------------
Continuously listens through the microphone for the wake phrase
"Hey Jarvis" using openWakeWord -- a free, fully local, open-source
wake word engine (no account or API key needed, unlike Porcupine).

Runs on ONNX Runtime, which has solid pre-built wheels for both
Windows and Raspberry Pi (ARM64), so this works unchanged on both.
"""

import onnxruntime as ort
import openwakeword
from openwakeword.model import Model
import sounddevice as sd

from config import WAKE_WORD_THRESHOLD

# openWakeWord's ONNX backend does GPU auto-discovery on init, which
# on the Pi logs noisy warnings like "Failed to detect devices under
# /sys/class/drm/card0" -- harmless (it just falls back to CPU), but
# clutters the console on every boot. Setting the logger to
# ERROR-only (severity 3) before the model loads suppresses those
# without hiding real errors.
ort.set_default_logger_severity(3)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # ~80ms of audio per chunk, the size openWakeWord expects

# After a detection, the model's internal buffers can still contain
# the tail (and room echo) of the phrase that just triggered it. If we
# start checking for matches immediately, this often causes an
# instant, unwanted re-trigger from the SAME utterance. Feeding it
# this many fresh chunks first (with predictions ignored) flushes
# those stale buffers before we start trusting its output again.
# 19 chunks * 80ms ~= 1.5 seconds.
WARMUP_CHUNKS = 19

_model = None


def _get_model() -> Model:
    """
    Lazily loads the openWakeWord model. The first time this ever
    runs, it downloads the pretrained model files from GitHub
    (a few MB, one-time, needs internet). After that, it loads
    instantly from the local cache.
    """
    global _model
    if _model is None:
        print("[WakeWord] Loading model (first run downloads it, one-time)...")
        openwakeword.utils.download_models()
        _model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    return _model


def listen_for_wake_word() -> None:
    """
    Blocks until "Hey Jarvis" is detected, then returns.
    Call this in a loop before each recording cycle.
    """
    model = _get_model()
    print("[WakeWord] Listening for 'Hey Jarvis'...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE
    ) as stream:
        # Flush any stale audio left in the model's internal buffers
        # from before this call (see WARMUP_CHUNKS comment above).
        for _ in range(WARMUP_CHUNKS):
            audio_chunk, _ = stream.read(CHUNK_SIZE)
            model.predict(audio_chunk.flatten())

        while True:
            audio_chunk, _ = stream.read(CHUNK_SIZE)
            audio_chunk = audio_chunk.flatten()

            predictions = model.predict(audio_chunk)

            for wake_word_name, score in predictions.items():
                if score > WAKE_WORD_THRESHOLD:
                    print(f"[WakeWord] Detected '{wake_word_name}' (score {score:.2f})")
                    model.reset()
                    return
