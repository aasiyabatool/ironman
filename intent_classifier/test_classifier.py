"""
intent_classifier/test_classifier.py
------------------------------------------
Interactive test: type any phrase and see what the classifier
predicts -- including phrasings you never explicitly listed in
training_data.py. That generalization is the whole point of the ML
approach over plain string matching.

Usage:
    python -m intent_classifier.test_classifier
"""

from intent_classifier.predict import predict_intent

if __name__ == "__main__":
    print("Intent Classifier Test. Type 'exit' to quit.\n")

    while True:
        text = input("Text: ").strip()
        if text.lower() in ("exit", "quit"):
            break
        if not text:
            continue

        label, confidence = predict_intent(text)
        print(f"  -> {label} (confidence: {confidence:.1%})\n")
