"""
intent_classifier/predict.py
---------------------------------
Loads the trained intent classifier and predicts which helmet
command (if any) a piece of text is asking for.
"""

import os
import pickle

from intent_classifier.config import MODEL_PATH, INTENT_CONFIDENCE_THRESHOLD

_model = None


def _get_model():
    global _model
    if _model is None:
        if not os.path.isfile(MODEL_PATH):
            raise RuntimeError(
                "No trained intent classifier found. Run "
                "'python -m intent_classifier.train_model' first."
            )
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model


def predict_intent(text: str) -> tuple:
    """
    Predicts the command intent for a piece of text.

    Returns:
        (label: str, confidence: float)
        If confidence is below INTENT_CONFIDENCE_THRESHOLD, label is
        forced to "NONE" regardless of the model's top guess -- this
        avoids misfiring a helmet command on a shaky prediction.
    """
    model = _get_model()

    probabilities = model.predict_proba([text])[0]
    classes = model.classes_

    best_index = probabilities.argmax()
    predicted_label = classes[best_index]
    confidence = probabilities[best_index]

    if confidence < INTENT_CONFIDENCE_THRESHOLD:
        return "NONE", confidence

    return predicted_label, confidence
