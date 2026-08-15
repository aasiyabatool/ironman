"""
vision/train_model.py
------------------------
Trains OpenCV's LBPH (Local Binary Patterns Histograms) face
recognizer using every photo inside training_faces/<name>/ folders,
and saves the trained model + the label-id -> name mapping to disk.

Run this after enrolling one or more people, or let enroll_face.py
call it automatically.

Usage:
    python -m vision.train_model
"""

import os

import cv2
import numpy as np

from vision.config import TRAINING_FACES_DIR, FACE_MODEL_PATH
from vision.utils import load_labels, save_labels, name_to_label_id


def train() -> None:
    if not os.path.isdir(TRAINING_FACES_DIR) or not os.listdir(TRAINING_FACES_DIR):
        print("[Train] No training photos found. Run enroll_face.py first.")
        return

    labels = load_labels()
    face_samples = []
    label_ids = []

    people = sorted(
        p for p in os.listdir(TRAINING_FACES_DIR)
        if os.path.isdir(os.path.join(TRAINING_FACES_DIR, p))
    )
    print(f"[Train] Found {len(people)} enrolled person(s): {', '.join(people)}")

    for person_name in people:
        person_dir = os.path.join(TRAINING_FACES_DIR, person_name)

        label_id = name_to_label_id(labels, person_name)
        labels[label_id] = person_name

        photo_files = [f for f in os.listdir(person_dir) if f.lower().endswith((".jpg", ".png"))]
        print(f"[Train]  - {person_name}: {len(photo_files)} photos (label id {label_id})")

        for photo_file in photo_files:
            photo_path = os.path.join(person_dir, photo_file)
            img = cv2.imread(photo_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            face_samples.append(img)
            label_ids.append(label_id)

    if not face_samples:
        print("[Train] No valid photos to train on.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(face_samples, np.array(label_ids))
    recognizer.save(FACE_MODEL_PATH)
    save_labels(labels)

    print(f"[Train] Model trained on {len(face_samples)} photos across {len(people)} people.")
    print(f"[Train] Saved model to {FACE_MODEL_PATH}")


if __name__ == "__main__":
    train()
