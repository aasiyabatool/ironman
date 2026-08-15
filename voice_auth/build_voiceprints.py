"""
voice_auth/build_voiceprints.py
------------------------------------
Builds a "voiceprint" (average embedding) for each enrolled person,
using voice_auth/enroll.py's recordings under voice_auth_data/<name>/.

This replaces train_model.py: there's no classifier to fit here.
Each person's voiceprint is just the mean of their sample
embeddings. At verification time (embedding_verify.py), a live clip
is compared against every voiceprint via cosine similarity, and the
closest match above the threshold wins.

Note: unlike train_model.py, this does NOT need an "unknown" class
-- resemblyzer's pretrained encoder already generalizes to voices it
has never seen, so there's nothing to learn about "not authorized."
You can skip enrolling "unknown" entirely with this approach. (A
small set of real impostor recordings is still useful later for
*tuning EMBEDDING_THRESHOLD* -- see the note at the bottom of this
file -- but it's not required to build voiceprints.)

Usage:
    python -m voice_auth.build_voiceprints
"""

import os
import pickle

import numpy as np

from voice_auth.config import TRAINING_DATA_DIR, VOICEPRINTS_PATH, UNKNOWN_LABEL
from voice_auth.embeddings import extract_embedding


def _person_embeddings(person_dir: str) -> list:
    embeddings = []
    for filename in os.listdir(person_dir):
        if not filename.lower().endswith((".wav", ".mp3")):
            continue
        path = os.path.join(person_dir, filename)
        try:
            embeddings.append(extract_embedding(path))
        except Exception as e:
            print(f"[Voiceprints] Skipping {filename}: {e}")
    return embeddings


def build() -> None:
    people = sorted(
        d for d in os.listdir(TRAINING_DATA_DIR)
        if os.path.isdir(os.path.join(TRAINING_DATA_DIR, d)) and d != UNKNOWN_LABEL
    )

    if not people:
        print(
            "[Voiceprints] No enrolled people found. Run "
            "'python -m voice_auth.enroll' first."
        )
        return

    voiceprints = {}

    for person in people:
        person_dir = os.path.join(TRAINING_DATA_DIR, person)
        embeddings = _person_embeddings(person_dir)

        if not embeddings:
            print(f"[Voiceprints]  - {person}: 0 usable samples, skipping")
            continue

        centroid = np.mean(embeddings, axis=0)
        voiceprints[person] = centroid
        print(f"[Voiceprints]  - {person}: {len(embeddings)} samples averaged")

    if not voiceprints:
        print("[Voiceprints] No usable voiceprints built.")
        return

    with open(VOICEPRINTS_PATH, "wb") as f:
        pickle.dump(voiceprints, f)

    print(f"\n[Voiceprints] Saved {len(voiceprints)} voiceprint(s) to {VOICEPRINTS_PATH}")
    print(
        "\nNext: tune EMBEDDING_THRESHOLD in config.py by testing with your "
        "own voice (genuine attempts) and a few other people's voices "
        "(impostor attempts) via 'python -m voice_auth.embedding_verify', "
        "and adjust until genuine attempts consistently score above the "
        "threshold and impostor attempts consistently score below it."
    )


if __name__ == "__main__":
    build()
