"""
vision/face_greeter.py
-------------------------
Combines live face recognition with JARVIS's voice: when a known
person's face is recognized, JARVIS speaks a greeting out loud
through the speaker.

This ties together three previously separate pieces:
  - vision/live_recognition.py's face detection + recognition logic
  - ai/text_to_speech.py to generate the spoken greeting
  - audio/player.py to actually play it

Usage:
    python -m vision.face_greeter

Controls:
    q - quit
    a - add ("enroll") a new person, then automatically resumes
"""

import os
import time

import cv2

from vision.config import FACE_MODEL_PATH, CONFIDENCE_THRESHOLD, GREET_COOLDOWN_SECONDS
from vision.utils import get_face_detector, load_labels
from vision.enroll_face import enroll
from vision.train_model import train

from ai.text_to_speech import synthesize
from audio.player import play
from audio.audio_utils import unique_response_path
from config import RESPONSES_DIR


def _load_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if os.path.isfile(FACE_MODEL_PATH):
        recognizer.read(FACE_MODEL_PATH)
        return recognizer, True
    return recognizer, False


def _greet(name: str) -> None:
    """Speaks a short JARVIS-style greeting for a newly recognized person."""
    message = f"Welcome back, {name}."
    print(f"[Greeter] Recognized {name} -> speaking greeting")
    try:
        audio_path = synthesize(message, unique_response_path(RESPONSES_DIR))
        play(audio_path)
    except Exception as e:
        print(f"[Greeter] Could not speak greeting: {e}")


def run() -> None:
    detector = get_face_detector()
    recognizer, has_model = _load_recognizer()
    labels = load_labels()

    if not has_model:
        print("[Greeter] No trained model found yet. Enroll someone first (press 'a').")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam. Check it's connected and not in use.")

    last_greeted = {}  # name -> unix timestamp of last greeting

    print("\n[Greeter] Running. Press 'a' to enroll a new face, 'q' to quit.\n")

    while True:
        ok, frame = cam.read()
        if not ok:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]
            name = "Unknown"
            color = (0, 0, 255)  # red for unknown

            if has_model:
                label_id, confidence = recognizer.predict(face_img)
                # For LBPH, a LOWER confidence score means a BETTER match.
                if confidence < CONFIDENCE_THRESHOLD and label_id in labels:
                    name = labels[label_id]
                    color = (0, 255, 0)  # green for recognized

                    now = time.time()
                    if now - last_greeted.get(name, 0) > GREET_COOLDOWN_SECONDS:
                        last_greeted[name] = now
                        _greet(name)

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, name, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, "Press 'a' to add new face, 'q' to quit", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("JARVIS Face Recognition + Greeting", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("a"):
            cam.release()
            cv2.destroyAllWindows()

            new_name = input("\nEnter the name of the new person: ").strip()
            if new_name:
                enroll(new_name)
                train()
                recognizer, has_model = _load_recognizer()
                labels = load_labels()

            cam = cv2.VideoCapture(0)
            print("\n[Greeter] Resumed. Press 'a' to enroll a new face, 'q' to quit.\n")

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
