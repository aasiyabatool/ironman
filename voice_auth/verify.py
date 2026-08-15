"""
voice_auth/verify.py
------------------------
Identifies WHICH enrolled person is speaking (or determines it's
nobody enrolled), using the trained multi-class SVM model.
"""

import os
import pickle

from voice_auth.config import MODEL_PATH, VOICE_AUTH_THRESHOLD, UNKNOWN_LABEL
from voice_auth.features import extract_features

_model = None


def _get_model():
    global _model
    if _model is None:
        if not os.path.isfile(MODEL_PATH):
            raise RuntimeError(
                "No trained voice auth model found. Run "
                "'python -m voice_auth.train_model' first."
            )
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model


def identify_speaker(audio_path: str) -> tuple:
    """
    Returns (predicted_label: str, confidence: float) -- the most
    likely enrolled person (or "unknown"), and the model's estimated
    probability for that specific prediction.
    """
    model = _get_model()
    features = extract_features(audio_path).reshape(1, -1)

    probabilities = model.predict_proba(features)[0]
    classes = model.classes_

    best_index = probabilities.argmax()
    predicted_label = classes[best_index]
    confidence = probabilities[best_index]

    return predicted_label, confidence


def is_authorized(audio_path: str, authorized_names: list = None) -> tuple:
    """
    Checks whether the given clip belongs to an authorized person.

    Args:
        audio_path: path to the audio clip to check.
        authorized_names: list of enrolled names that count as
            "authorized" (e.g. ["aasiya", "friend_name"]). If None,
            ANY identified person other than "unknown" is treated as
            authorized -- useful if every name you've enrolled should
            be allowed to command the helmet.

    Returns:
        (is_authorized: bool, identified_name: str, confidence: float)
    """
    predicted_label, confidence = identify_speaker(audio_path)

    meets_threshold = confidence >= VOICE_AUTH_THRESHOLD
    is_known_person = predicted_label != UNKNOWN_LABEL

    if authorized_names is not None:
        is_known_person = is_known_person and predicted_label in authorized_names

    authorized = meets_threshold and is_known_person

    return authorized, predicted_label, confidence
