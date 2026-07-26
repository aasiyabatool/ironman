"""
vision/config.py
------------------
Settings for the face enrollment / recognition system.
Kept separate from the main config.py since this is an optional
module not yet wired into the voice assistant pipeline.
"""

import os

VISION_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(VISION_DIR)

TRAINING_FACES_DIR = os.path.join(BASE_DIR, "training_faces")
MODELS_DIR = os.path.join(BASE_DIR, "models")

FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_model.yml")
FACE_LABELS_PATH = os.path.join(MODELS_DIR, "face_labels.json")

# Number of photos captured per person during enrollment
PHOTOS_PER_PERSON = 30

# How many camera frames to wait between automatic captures
# (avoids saving several near-identical photos in a row)
CAPTURE_INTERVAL_FRAMES = 5

# LBPH recognizer: LOWER confidence score = a BETTER match (this is
# a distance score, not a percentage). Below this threshold, a face
# is considered "recognized"; at or above it, "Unknown". If real
# people are showing as Unknown too often, raise this number; if
# strangers are being recognized as known people, lower it.
CONFIDENCE_THRESHOLD = 70

# How long (in seconds) to wait before greeting the SAME person again.
# Without this, JARVIS would say "Welcome back" dozens of times per
# second while your face stays in frame.
GREET_COOLDOWN_SECONDS = 300  # 5 minutes

for folder in (TRAINING_FACES_DIR, MODELS_DIR):
    os.makedirs(folder, exist_ok=True)
