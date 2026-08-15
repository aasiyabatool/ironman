"""
voice_auth/embedding_verify.py
------------------------------------
Identifies who's speaking by comparing a live clip's embedding
against each enrolled person's voiceprint (see build_voiceprints.py)
using cosine similarity -- the embedding-based counterpart to
verify.py's SVM classification.

Also runnable directly for a quick live mic test, the same way
live_test.py exercises the SVM pipeline:

    python -m voice_auth.embedding_verify
"""

import os
import pickle

import sounddevice as sd
from scipy.io.wavfile import write as wav_write

from voice_auth.config import (
    VOICEPRINTS_PATH, EMBEDDING_THRESHOLD, SAMPLE_RATE, RECORD_SECONDS,
    TRAINING_DATA_DIR,
)
from voice_auth.embeddings import extract_embedding, cosine_similarity

_voiceprints = None


def _get_voiceprints() -> dict:
    global _voiceprints
    if _voiceprints is None:
        if not os.path.isfile(VOICEPRINTS_PATH):
            raise RuntimeError(
                "No voiceprints found. Run "
                "'python -m voice_auth.build_voiceprints' first."
            )
        with open(VOICEPRINTS_PATH, "rb") as f:
            _voiceprints = pickle.load(f)
    return _voiceprints


def identify_speaker(audio_path: str) -> tuple:
    """
    Returns (best_match_name: str, similarity: float) -- whichever
    enrolled voiceprint the clip is closest to, and how close
    (cosine similarity, roughly 0-1; higher is more similar).
    """
    voiceprints = _get_voiceprints()
    embedding = extract_embedding(audio_path)

    best_name = None
    best_score = -1.0
    for name, voiceprint in voiceprints.items():
        score = cosine_similarity(embedding, voiceprint)
        if score > best_score:
            best_name, best_score = name, score

    return best_name, best_score


def is_authorized(audio_path: str, authorized_names: list = None) -> tuple:
    """
    Checks whether the given clip belongs to an authorized person.

    Args:
        audio_path: path to the audio clip to check.
        authorized_names: list of enrolled names that count as
            "authorized". If None, the best match being above
            EMBEDDING_THRESHOLD is enough (i.e. every enrolled
            person is authorized).

    Returns:
        (is_authorized: bool, matched_name: str, similarity: float)
    """
    matched_name, similarity = identify_speaker(audio_path)

    meets_threshold = similarity >= EMBEDDING_THRESHOLD
    is_allowed_name = authorized_names is None or matched_name in authorized_names

    authorized = meets_threshold and is_allowed_name

    return authorized, matched_name, similarity


def _record_test_clip() -> str:
    path = os.path.join(TRAINING_DATA_DIR, "_live_test_clip.wav")
    print(f"\nSpeak now ({RECORD_SECONDS} seconds)...")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    wav_write(path, SAMPLE_RATE, audio)
    return path


if __name__ == "__main__":
    print("Voice Authentication Live Test (embedding-based)")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            input("Press Enter, then speak...")
            clip_path = _record_test_clip()

            authorized, name, similarity = is_authorized(clip_path)

            if authorized:
                print(f"AUTHORIZED: {name} (similarity: {similarity:.2f})\n")
            else:
                print(f"NOT AUTHORIZED (closest match: {name}, similarity: {similarity:.2f})\n")

    except KeyboardInterrupt:
        print("\nStopped.")
