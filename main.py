"""
main.py
--------
Entry point for JARVIS -- wake-word activated, with true barge-in.

Combat Mode and Party Mode are persistent LED states -- see the
PERSISTENT_LED_COMMANDS note in run_once() below.

Voice authentication flow: on boot, JARVIS explicitly announces it's
waiting for authentication and waits for a "Hey Jarvis" + speech
clip. That FIRST clip is used ONLY to verify the speaker (see
voice_auth/embedding_verify.py) -- it is never transcribed or acted
on as a command. If it passes, the session is trusted for the rest
of the run and JARVIS drops into normal wake-word command handling.
If it fails, JARVIS speaks a refusal and shuts the whole system down.

NOTE: torch (pulled in by voice_auth -> resemblyzer) must be imported
BEFORE onnxruntime (pulled in by ai.speech_to_text) -- both ship their
own BLAS build on aarch64, and whichever loads first wins the process-
wide symbol table. Importing torch second causes an
"undefined symbol: sbgemm_" crash. Do not reorder these imports.
"""

import threading

# Must come before ai.speech_to_text (onnxruntime) -- see note above.
from voice_auth.config import VOICE_AUTH_ENABLED
from voice_auth.embedding_verify import is_authorized

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

# Only these enrolled voiceprints (see voice_auth/build_voiceprints.py)
# are allowed to issue commands -- edit this list as you enroll more people.
AUTHORIZED_NAMES = ["aasiya"]


def authenticate_session(state: SharedState) -> bool:
    """
    Speaks an explicit auth prompt, then blocks until the first
    wake-word-triggered clip arrives and checks it against the
    enrolled voiceprint(s). Returns True if authorized.

    This clip is consumed here and ONLY here -- it is never passed
    to transcribe()/detect_command(), so saying "Hey Jarvis, turn on
    the lights" as your very first utterance authenticates you but
    does not also execute "turn on the lights" as a side effect.
    """
    set_status("listening")
    prompt = "Awaiting voice authentication. Say only Hey Jarvis, nothing else, to authenticate."
    print(f"JARVIS: {prompt}")
    audio_reply = synthesize(prompt, unique_response_path(RESPONSES_DIR))
    play_interruptible(audio_reply, state)

    print("[Main] Waiting for 'Hey Jarvis' to authenticate (say nothing else)...")
    audio_path = state.auth_queue.get()  # blocks until the wake-word clip arrives
    state.interrupt_requested.clear()

    authorized, matched_name, similarity = is_authorized(
        audio_path, authorized_names=AUTHORIZED_NAMES
    )
    print(
        f"[VoiceAuth] closest match: {matched_name} "
        f"(similarity: {similarity:.2f}) -> "
        f"{'AUTHORIZED' if authorized else 'REJECTED'}"
    )

    if authorized:
        greeting = f"Welcome back, {matched_name}."
        print(f"JARVIS: {greeting}")
        log_interaction("[auth clip]", "AUTH_SUCCESS", greeting)
        audio_reply = synthesize(greeting, unique_response_path(RESPONSES_DIR))
        play_interruptible(audio_reply, state)
        # Hand control back to normal command capture -- from here on,
        # wake words trigger trailing-speech recording as usual.
        state.auth_mode.clear()
        set_status("ready")
        return True

    refusal = "You are not authorized. Shutting down."
    print(f"JARVIS: {refusal}")
    log_interaction("[auth clip]", "AUTH_REJECTED_SHUTDOWN", refusal)
    audio_reply = synthesize(refusal, unique_response_path(RESPONSES_DIR))
    play_interruptible(audio_reply, state)
    set_status("error")
    return False


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

    if VOICE_AUTH_ENABLED:
        authorized = authenticate_session(state)
        if not authorized:
            state.shutdown_requested.set()
            return
    else:
        # No auth stage to clear auth_mode for us -- clear it now so
        # the audio thread treats every wake word as a normal command
        # capture instead of waiting for an auth clip forever.
        state.auth_mode.clear()
        print("[Main] Voice authentication DISABLED (set VOICE_AUTH_ENABLED=true to turn on).\n")

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
