"""
intent_classifier/train_model.py
-------------------------------------
Trains an optimized TF-IDF + Logistic Regression text classifier to recognize
which helmet command (if any) a piece of text is asking for.

Usage:
    python -m intent_classifier.train_model
"""

import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, StratifiedKFold

from intent_classifier.config import MODEL_PATH
from intent_classifier.training_data import TRAINING_EXAMPLES


def train() -> None:
    texts = []
    labels = []

    for label, examples in TRAINING_EXAMPLES.items():
        texts.extend(examples)
        labels.extend([label] * len(examples))

    print(f"[Train] Total training examples: {len(texts)}")
    for label, examples in TRAINING_EXAMPLES.items():
        print(f"[Train]   - {label}: {len(examples)} examples")

    pipeline = Pipeline([
        # 1. Using char_wb (character n-grams inside word boundaries) allows the 
        # model to recognize word roots like "lift", "vis", "face", "plate" even if 
        # STT introduces typos or compound word shifts ("faceplate" vs "face plate").
        # 2. Removed stop_words="english" because directional words like "on", "off", 
        # "up", and "down" are essential to separate contrasting intents.
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 5),
            lowercase=True,
            sublinear_tf=True
        )),
        # C=10.0 increases weight on explicit intent features. 
        # class_weight="balanced" prevents "NONE" from dominating predictions.
        ("classifier", LogisticRegression(
            C=10.0,
            max_iter=1000,
            class_weight="balanced"
        )),
    ])

    print("\n[Train] Running 5-fold cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, texts, labels, cv=cv)

    print(f"[Train] Cross-validation accuracy: {cv_scores.mean():.2%} "
          f"(individual folds: {', '.join(f'{s:.0%}' for s in cv_scores)})")

    print("\n[Train] Training final model on all available data...")
    pipeline.fit(texts, labels)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)

    print(f"[Train] Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()