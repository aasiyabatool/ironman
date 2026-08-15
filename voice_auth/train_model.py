"""
voice_auth/train_model.py
-----------------------------
Trains a MULTI-CLASS SVM to identify WHICH enrolled person is
speaking (or "unknown" if nobody enrolled matches well), using MFCC
features from every voice_auth_data/<name>/ folder -- however many
people you've enrolled.

Usage:
    python -m voice_auth.train_model
"""

import os
import pickle

import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from voice_auth.config import TRAINING_DATA_DIR, MODEL_PATH
from voice_auth.features import extract_features


def _load_samples(directory: str):
    features = []

    for filename in os.listdir(directory):
        if not filename.lower().endswith((".wav", ".mp3")):
            continue
        path = os.path.join(directory, filename)
        try:
            features.append(extract_features(path))
        except Exception as e:
            print(f"[Train] Skipping {filename}: {e}")

    return features


def train() -> None:
    people = sorted(
        d for d in os.listdir(TRAINING_DATA_DIR)
        if os.path.isdir(os.path.join(TRAINING_DATA_DIR, d))
    )

    if len(people) < 2:
        print(
            "[Train] Need at least 2 classes to train (e.g. your name + "
            "'unknown'). Run 'python -m voice_auth.enroll' to add people first."
        )
        return

    print(f"[Train] Found {len(people)} classes: {', '.join(people)}")

    all_features = []
    all_labels = []

    for person in people:
        person_dir = os.path.join(TRAINING_DATA_DIR, person)
        features = _load_samples(person_dir)
        print(f"[Train]  - {person}: {len(features)} samples")
        all_features.extend(features)
        all_labels.extend([person] * len(features))

    if len(all_features) < 10:
        print("[Train] Not enough total samples yet across all classes.")
        return

    X = np.array(all_features)
    y = np.array(all_labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[Train] Training multi-class SVM classifier...")
    # class_weight="balanced" matters since classes will likely have
    # uneven sample counts (e.g. lots of synthetic "unknown" samples
    # vs. fewer real recordings per enrolled person).
    model = SVC(kernel="rbf", probability=True, class_weight="balanced")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"\n[Train] Test accuracy: {accuracy:.2%}")
    print(classification_report(y_test, predictions))

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"[Train] Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
