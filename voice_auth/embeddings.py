"""
voice_auth/embeddings.py
----------------------------
Extracts a fixed-length speaker embedding from an audio clip using
resemblyzer's pretrained voice encoder (the GE2E-trained model from
the "Real-Time Voice Cloning" project, built specifically for
speaker verification/diarization -- as opposed to the hand-crafted
MFCC statistics in features.py).

Because the encoder was already trained on thousands of real
speakers, embeddings for two clips of the SAME person's voice end up
close together in the embedding space (high cosine similarity),
while embeddings for DIFFERENT people end up farther apart --
without needing you to have taught it what "not authorized" sounds
like, the way the MFCC+SVM pipeline required a representative
"unknown" class.

This replaces train_model.py's classification approach with
similarity matching -- see build_voiceprints.py and
embedding_verify.py.
"""

import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav

_encoder = None


def _get_encoder() -> "VoiceEncoder":
    global _encoder
    if _encoder is None:
        # Loads the pretrained weights once per process. CPU-only is
        # fine -- this model is small and inference on a few seconds
        # of audio takes well under a second even on a Pi.
        _encoder = VoiceEncoder()
    return _encoder


def extract_embedding(audio_path: str) -> np.ndarray:
    """
    Loads an audio file and returns its 256-dimensional speaker
    embedding (a unit-normalized vector -- cosine similarity between
    two embeddings is just their dot product).
    """
    wav = preprocess_wav(audio_path)
    encoder = _get_encoder()
    return encoder.embed_utterance(wav)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    resemblyzer embeddings are already unit-normalized, so this is
    just the dot product -- but normalizing explicitly here makes
    the function safe to reuse even if that ever changes upstream.
    """
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)
    return float(np.dot(a_norm, b_norm))
