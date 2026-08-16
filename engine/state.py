"""
engine/state.py
-------------------
Shared threading primitives that coordinate the always-on
background audio thread with the main thread (which handles
transcription, Gemini, and speech).
"""

import threading
import queue


class SharedState:
    def __init__(self):
        # Queue of captured command .wav paths, filled by the audio
        # thread and drained by the main thread. Using a real queue
        # (instead of a single Event + variable) means a command
        # captured while main.py is still busy on a previous one
        # (transcribe -> Gemini -> TTS can take a few seconds) waits
        # its turn instead of silently getting overwritten/dropped.
        self.command_queue = queue.Queue()

        # Set (True) until voice authentication succeeds. While set,
        # the audio thread does NOT record any trailing speech after
        # the wake word -- it just snapshots the rolling buffer that
        # already contains the "Hey Jarvis" utterance itself and
        # queues that for auth. Cleared by main.py once authentication
        # passes, after which the audio thread goes back to capturing
        # normal trailing commands.
        self.auth_mode = threading.Event()
        self.auth_mode.set()

        # Queue of captured auth-clip .wav paths (wake word phrase
        # only), filled by the audio thread while auth_mode is set
        # and drained by main.py's authenticate_session().
        self.auth_queue = queue.Queue()

        # Set by the audio thread the instant a NEW wake word is heard,
        # so any currently-playing response stops immediately (barge-in).
        self.interrupt_requested = threading.Event()

        # Set for as long as a response is actively playing through the
        # speaker. Used to raise the wake-word threshold during playback,
        # so JARVIS's own voice bleeding into the mic is much less likely
        # to falsely re-trigger itself (see engine/audio_stream.py).
        self.is_speaking = threading.Event()

        # Set to tell all background loops to stop (clean shutdown).
        self.shutdown_requested = threading.Event()

        # Both JARVIS's own responses and the camera's spoken greetings
        # use the same physical speaker. This lock ensures only one of
        # them is ever actually playing audio at a time.
        self.speaker_lock = threading.Lock()
