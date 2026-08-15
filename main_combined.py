"""
main_combined.py
-------------------
Runs JARVIS's full experience: continuous wake-word listening with
voice commands (barge-in enabled) AND continuous camera-based face
recognition with spoken greetings -- all at the same time.

Three concurrent pieces of work:

    Thread 1 (background) -- engine/audio_stream.py:
        Owns the microphone. Listens for "Hey Jarvis" and captures
        the command that follows.

    Thread 2 (background) -- voice command processor:
        Waits for a captured command and runs it through
        Whisper -> command parser / Gemini -> text-to-speech ->
        interruptible playback.

    Main thread -- camera / face greeter:
        Continuously watches the webcam and greets recognized faces
        by name through the speaker. Press 'a' to enroll a new
        person, 'q' to quit (this also stops the background threads).

Both the voice processor and the camera greeter can speak through
the SAME speaker, so they share state.speaker_lock to avoid talking
over each other. Saying "Hey Jarvis" at any time interrupts whichever
one is currently talking -- true barge-in, now covering greetings
too, not just JARVIS's own responses.

This is a separate entry point from main.py on purpose: main.py
(voice only) stays untouched and known-working. Once this combined
version has been tested and trusted, main.py can simply be replaced
with it.
"""

import os
import threading
import time

import cv2

from config import RESPONSES_DIR
from engine.state import SharedState
from engine import audio_stream
from engine.player_control import play_interruptible

from ai.speech_to_text import transcribe, preload_model
from ai.gemini_client import ask
from ai.text_to_speech import synthesize
from ai.conversation import log_interaction
from audio.audio_utils import unique_response_path
from commands.parser import detect_command
from commands.simulator import execute_command
from commands.helmet_commands import NONE

from vision.config import FACE_MODEL_PATH, CONFIDENCE_THRESHOLD, GREET_COOLDOWN_SECONDS
from vision.utils import get_face_detector, load_labels
from vision.enroll_face import enroll
from vision.train_model import train


# ---------------------------------------------------------------
# Shared speech helper -- used by both voice responses and greetings
# ---------------------------------------------------------------

def speak(text: str, state: SharedState) -> None:
    audio_path = synthesize(text, unique_response_path(RESPONSES_DIR))
    play_interruptible(audio_path, state)


# ---------------------------------------------------------------
# Voice command processing (runs in its own background thread)
# ---------------------------------------------------------------

def run_voice_command(state: SharedState, audio_path: str) -> None:
    """Processes one already-captured command recording."""
    text = transcribe(audio_path)

    if not text:
        print("[Voice] No speech detected. Say 'Hey Jarvis' to try again.")
        return

    command = detect_command(text)

    if command != NONE:
        response_text = execute_command(command)
        print(f"JARVIS: {response_text}")
        log_interaction(text, command, response_text)
        speak(response_text, state)
    else:
        reply = ask(text)
        print(f"JARVIS: {reply}")
        log_interaction(text, "NONE", reply)
        speak(reply, state)


def voice_processor_loop(state: SharedState) -> None:
    """Background thread: waits for captured commands and handles them."""
    while not state.shutdown_requested.is_set():
        got_command = state.command_ready.wait(timeout=0.5)
        if not got_command:
            continue  # just a timeout check for shutdown, loop again

        state.command_ready.clear()
        audio_path = state.pending_command_path
        state.interrupt_requested.clear()

        # Voice responses always get to speak eventually -- wait for
        # the speaker if the camera greeter happens to be mid-greeting.
        with state.speaker_lock:
            run_voice_command(state, audio_path)


# ---------------------------------------------------------------
# Camera / face recognition + greeting (runs on the MAIN thread --
# OpenCV's imshow/waitKey are safest kept on the main thread)
# ---------------------------------------------------------------

def _load_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if os.path.isfile(FACE_MODEL_PATH):
        recognizer.read(FACE_MODEL_PATH)
        return recognizer, True
    return recognizer, False


def camera_loop(state: SharedState) -> None:
    detector = get_face_detector()
    recognizer, has_model = _load_recognizer()
    labels = load_labels()

    if not has_model:
        print("[Camera] No trained model found yet. Every face will show as 'Unknown' "
              "until you enroll someone (press 'a').")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam. Check it's connected and not in use.")

    last_greeted = {}  # name -> unix timestamp of last greeting

    print("\n[Camera] Running. Press 'a' to enroll a new face, 'q' to quit.\n")

    while not state.shutdown_requested.is_set():
        ok, frame = cam.read()
        if not ok:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]
            name = "Unknown"
            color = (0, 0, 255)

            if has_model:
                label_id, confidence = recognizer.predict(face_img)
                if confidence < CONFIDENCE_THRESHOLD and label_id in labels:
                    name = labels[label_id]
                    color = (0, 255, 0)

                    now = time.time()
                    if now - last_greeted.get(name, 0) > GREET_COOLDOWN_SECONDS:
                        # Don't block the camera loop waiting for the
                        # speaker -- if it's busy (JARVIS mid-response),
                        # just skip this greeting. The cooldown means
                        # we'll get another chance again soon.
                        if state.speaker_lock.acquire(blocking=False):
                            try:
                                last_greeted[name] = now
                                print(f"[Camera] Recognized {name} -> greeting")
                                speak(f"Welcome back, {name}.", state)
                            finally:
                                state.speaker_lock.release()

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, name, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, "Press 'a' to add new face, 'q' to quit", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("JARVIS", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            state.shutdown_requested.set()
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
            print("\n[Camera] Resumed. Press 'a' to enroll a new face, 'q' to quit.\n")

    cam.release()
    cv2.destroyAllWindows()


# ---------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print(" JARVIS AI — Voice (barge-in) + Face Recognition, combined")
    print("=" * 60)
    print("Say 'Hey Jarvis' anytime to talk. The camera window greets")
    print("recognized faces automatically. Press 'q' in the camera")
    print("window to quit everything.\n")

    # Load the Whisper model now, during boot, so the first "Hey Jarvis"
    # doesn't stall while the model loads on top of transcription.
    preload_model()

    state = SharedState()

    audio_thread = threading.Thread(target=audio_stream.run, args=(state,), daemon=True)
    voice_thread = threading.Thread(target=voice_processor_loop, args=(state,), daemon=True)

    audio_thread.start()
    voice_thread.start()

    try:
        camera_loop(state)  # runs on the main thread
    except KeyboardInterrupt:
        state.shutdown_requested.set()

    print("\n[Main] Shutting down JARVIS. Goodbye.")


if __name__ == "__main__":
    main()
