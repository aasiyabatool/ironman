"""
voice_auth/generate_synthetic_negatives.py
----------------------------------------------
Generates "unknown" (non-authorized) training samples using
text-to-speech, saved into voice_auth_data/unknown/. This bootstraps
your "not an authorized person" class without needing to round up
many real other speakers -- though a few real ones (via enroll.py,
name "unknown") will still help the model generalize better.

Usage:
    python -m voice_auth.generate_synthetic_negatives
"""

from gtts import gTTS

from voice_auth.config import UNKNOWN_DIR

PHRASES = [
    "Hello, how are you today?",
    "The weather is quite nice this afternoon.",
    "Can you help me with something?",
    "I am testing this voice recognition system.",
    "This is a sample sentence for training.",
    "Please open the door for me.",
    "What time is it right now?",
    "I would like a cup of coffee.",
    "The quick brown fox jumps over the lazy dog.",
    "Artificial intelligence is an interesting field.",
    "Turn on the lights in the room.",
    "This system is currently being tested.",
    "Good morning, I hope you slept well.",
    "The meeting has been rescheduled to tomorrow.",
    "Thank you very much for your help today.",
]


def generate() -> None:
    print(f"Generating {len(PHRASES)} synthetic 'unknown' samples...")

    for i, phrase in enumerate(PHRASES, start=1):
        tts = gTTS(text=phrase, lang="en")
        path = f"{UNKNOWN_DIR}/synthetic_{i}.mp3"
        tts.save(path)
        print(f"Saved: {path}")

    print(f"\nDone. {len(PHRASES)} synthetic samples added to {UNKNOWN_DIR}")
    print("Tip: a few REAL recordings of other people")
    print("(python -m voice_auth.enroll, name 'unknown') help even more.")


if __name__ == "__main__":
    generate()
