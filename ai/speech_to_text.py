"""
ai/speech_to_text.py
---------------------
Converts recorded speech (voice.wav) into text using faster-whisper
(a CTranslate2 reimplementation of Whisper). Runs fully offline once
the model weights are downloaded.

Switched from openai-whisper to faster-whisper for a 2-4x speedup on
CPU-only ARM64 hardware (Raspberry Pi) -- compute_type="int8" and
beam_size=1 trade a small amount of accuracy for that speed, which is
the right call for short voice commands where latency matters more
than transcript polish.
"""

from faster_whisper import WhisperModel

from config import WHISPER_MODEL_SIZE

_model = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        print(f"[STT] Loading faster-whisper model '{WHISPER_MODEL_SIZE}'...")
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def preload_model() -> None:
    """
    Loads the Whisper model into memory up front, during the initial
    boot sequence, instead of lazily on the user's first command.
    Call this once at startup so the first "Hey Jarvis" doesn't pay
    the model-load latency on top of transcription latency.
    """
    _get_model()
    print("[STT] Model preloaded and ready.")


def transcribe(audio_path: str) -> str:
    """
    Transcribes an audio file to text.

    Args:
        audio_path: path to a .wav file.

    Returns:
        The recognized text, stripped of leading/trailing whitespace.
    """
    model = _get_model()
    print("[STT] Transcribing...")
    segments, _info = model.transcribe(audio_path, beam_size=1)
    text = "".join(segment.text for segment in segments).strip()
    print(f"[STT] Recognized: \"{text}\"")
    return text
