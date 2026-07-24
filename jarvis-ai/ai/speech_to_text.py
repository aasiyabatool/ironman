"""
ai/speech_to_text.py
---------------------
Converts recorded speech (voice.wav) into text using
OpenAI's local Whisper model. Runs fully offline once the
model weights are downloaded.
"""

import whisper

from config import WHISPER_MODEL_SIZE

_model = None  # loaded lazily so `import` doesn't stall the program


def _get_model():
    global _model
    if _model is None:
        print(f"[STT] Loading Whisper model '{WHISPER_MODEL_SIZE}' (first run only)...")
        _model = whisper.load_model(WHISPER_MODEL_SIZE)
    return _model


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
    result = model.transcribe(audio_path, fp16=False)
    text = result.get("text", "").strip()
    print(f"[STT] Recognized: \"{text}\"")
    return text
