"""
vision/utils.py
------------------
Shared helpers for face detection, and loading/saving the
label-id -> name mapping used by the recognizer.
"""

import json
import os

import cv2

from vision.config import FACE_LABELS_PATH


def get_face_detector():
    """
    Loads OpenCV's built-in Haar Cascade face detector.
    This ships inside the opencv-contrib-python package itself,
    so no separate download is needed.
    """
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    return cv2.CascadeClassifier(cascade_path)


def load_labels() -> dict:
    """Returns {label_id (int): name (str)}. Empty dict if none saved yet."""
    if not os.path.isfile(FACE_LABELS_PATH):
        return {}
    with open(FACE_LABELS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def save_labels(labels: dict) -> None:
    """Saves {label_id (int): name (str)} to disk as JSON."""
    with open(FACE_LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in labels.items()}, f, indent=2)


def next_label_id(labels: dict) -> int:
    """Returns the next unused integer label id."""
    if not labels:
        return 0
    return max(labels.keys()) + 1


def name_to_label_id(labels: dict, name: str) -> int:
    """
    Returns the label id for a given name, reusing the existing id
    if this person was already enrolled before (e.g. re-enrolling
    to add more training photos for better accuracy).
    """
    for label_id, existing_name in labels.items():
        if existing_name.lower() == name.lower():
            return label_id
    return next_label_id(labels)
