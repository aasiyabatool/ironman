"""
vision/enroll_face.py
------------------------
Stand-alone enrollment tool: opens your webcam, captures a batch
of face photos for a named person, and saves them to
training_faces/<name>/. Run train_model.py afterward (or let this
script offer to do it automatically) to teach the recognizer the
new face.

Usage:
    python -m vision.enroll_face
"""

import os

import cv2

from vision.config import TRAINING_FACES_DIR, PHOTOS_PER_PERSON, CAPTURE_INTERVAL_FRAMES
from vision.utils import get_face_detector


def enroll(name: str, photo_count: int = PHOTOS_PER_PERSON) -> str:
    """
    Captures `photo_count` face photos for `name` using the webcam.
    Returns the folder path where photos were saved.
    """
    person_dir = os.path.join(TRAINING_FACES_DIR, name)
    os.makedirs(person_dir, exist_ok=True)

    existing_photos = len(os.listdir(person_dir))
    detector = get_face_detector()
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        raise RuntimeError("Could not open webcam. Check it's connected and not in use.")

    print(f"\n[Enroll] Capturing {photo_count} photos for '{name}'.")
    print("[Enroll] Look at the camera and slowly turn your head slightly "
          "left/right/up/down during capture for better accuracy.")
    print("[Enroll] Press 'q' at any time to stop early.\n")

    captured = 0
    frame_count = 0

    while captured < photo_count:
        ok, frame = cam.read()
        if not ok:
            continue

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if frame_count % CAPTURE_INTERVAL_FRAMES == 0:
                face_img = gray[y:y + h, x:x + w]
                photo_path = os.path.join(
                    person_dir, f"{name}_{existing_photos + captured:03d}.jpg"
                )
                cv2.imwrite(photo_path, face_img)
                captured += 1
                print(f"[Enroll] Captured photo {captured}/{photo_count}")

        cv2.putText(frame, f"Captured: {captured}/{photo_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Enrollment - press 'q' to stop", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()

    print(f"[Enroll] Done. Saved {captured} photos to {person_dir}\n")
    return person_dir


if __name__ == "__main__":
    person_name = input("Enter the name of the person to enroll: ").strip()
    if not person_name:
        print("No name entered, exiting.")
    else:
        enroll(person_name)

        train_now = input("Train the recognizer now with this new face? (y/n): ").strip().lower()
        if train_now == "y":
            from vision.train_model import train
            train()
