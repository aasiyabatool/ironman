"""
intent_classifier/config.py
--------------------------------
Settings for the command intent classifier.
"""

import os

INTENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(INTENT_DIR)

MODEL_PATH = os.path.join(BASE_DIR, "models", "intent_classifier.pkl")

# Minimum confidence required to trust the classifier's top guess.
# Below this, the result is forced to "NONE" (treated as general
# conversation) rather than risk misfiring a helmet command on a
# shaky, low-confidence prediction.
INTENT_CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.4"))

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
