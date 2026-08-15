"""
main.py
--------
Entry point for JARVIS -- wake-word activated, with true barge-in.

Combat Mode and Party Mode are persistent LED states -- see the
PERSISTENT_LED_COMMANDS note in run_once() below.
"""

import threading

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
from commands.helmet_commands import NONE, COMBAT_MODE, PARTY_MODE
from commands.status_led import set_status

# Commands that intentionally leave the LEDs in a persistent state --
# the automatic "back to ready" status update is skipped for these,
# so e.g. Combat Mode's red doesn't get overwritten a second after
# it's activated.
PERSISTENT_LED_COMMANDS = {COMBAT_MODE, PARTY_MODE}


def run_once(state: SharedState, audio_path: str) -> None:
    """Processes one already-captured command recording."""

    set_status("processing")

    try:
        text = transcribe(audio_path)

        if not text:
            print("[Main] No speech detected. Say 'Hey Jarvis' to try again.")
            set_status("ready")
            return

        command = detect_command(text)

        if command != NONE:
            response_text = execute_command(command)
            print(f"JARVIS: {response_text}")
            log_interaction(text, command, response_text)
            audio_reply = synthesize(response_text, unique_response_path(RESPONSES_DIR))
            play_interruptible(audio_reply, state)

        else:
            reply = ask(text)
            print(f"JARVIS: {reply}")
            log_interaction(text, "NONE", reply)

            audio_reply = synthesize(reply, unique_response_path(RESPONSES_DIR))
            play_interruptible(audio_reply, state)

        if command not in PERSISTENT_LED_COMMANDS:
            set_status("ready")

    except Exception as e:
        print(f"[Main] Error while processing command: {e}")
        set_status("error")


def main() -> None:
    print("=" * 50)
    print(" JARVIS AI Assistant — Wake-Word Activated (Barge-In Enabled)")
    print("=" * 50)
    print("Say 'Hey Jarvis' at any time -- even while JARVIS is talking --")
    print("to interrupt and start a new command. Press Ctrl+C to exit.\n")

    # Load the Whisper model now, during boot, so the first "Hey Jarvis"
    # doesn't stall while the model loads on top of transcription.
    preload_model()

    state = SharedState()

    listener_thread = threading.Thread(
        target=audio_stream.run, args=(state,), daemon=True
    )
    listener_thread.start()

    try:
        while True:
            audio_path = state.command_queue.get()  # blocks until a command is queued
            state.interrupt_requested.clear()

            run_once(state, audio_path)

    except KeyboardInterrupt:
        print("\n[Main] Shutting down JARVIS. Goodbye.")
        state.shutdown_requested.set()


if __name__ == "__main__":
    main()
