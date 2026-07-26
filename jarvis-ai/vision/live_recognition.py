"""
vision/live_recognition.py
-----------------------------
Live webcam face recognition. Draws a box + name around recognized
faces, and "Unknown" around unrecognized ones. Press 'a' at any time
to enroll whoever is currently in frame as a new person on the spot
-- no need to stop and run a separate script first.

Usage:
    python -m vision.live_recognition

Controls:
    q - quit
    a - add ("enroll") a new person, then automatically resumes
"""

import os

import cv2

from vision.config import FACE_MODEL_PATH, CONFIDENCE_THRESHOLD
from vision.utils import get_face_detector, load_labels
from vision.enroll_face import enroll
from vision.train_model import train


def _load_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if os.path.isfile(FACE_MODEL_PATH):
        recognizer.read(FACE_MODEL_PATH)
        return recognizer, True
    return recognizer, False


def run() -> None:
    detector = get_face_detector()
    recognizer, has_model = _load_recognizer()
    labels = load_labels()

    if not has_model:
        print("[Live] No trained model found yet. Every face will show as 'Unknown' "
              "until you enroll someone (press 'a').")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam. Check it's connected and not in use.")

    print("\n[Live] Running. Press 'a' to enroll a new face, 'q' to quit.\n")

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

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, name, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, "Press 'a' to add new face, 'q' to quit", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("JARVIS Face Recognition", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        elif key == ord("a"):
            # Release the camera while the terminal prompt is shown,
            # so the webcam LED/resource isn't held during typing.
            cam.release()
            cv2.destroyAllWindows()

            new_name = input("\nEnter the name of the new person: ").strip()
            if new_name:
                enroll(new_name)
                train()
                # Reload the freshly trained model + labels before resuming
                recognizer, has_model = _load_recognizer()
                labels = load_labels()

            cam = cv2.VideoCapture(0)
            print("\n[Live] Resumed. Press 'a' to enroll a new face, 'q' to quit.\n")

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
