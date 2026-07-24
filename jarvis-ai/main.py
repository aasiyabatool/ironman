"""
main.py
--------
Entry point for the Phase 1 JARVIS software prototype.

Pipeline:

    Record audio (laptop mic)
        -> Whisper speech-to-text
            -> Command parser
                -> Helmet command?  --yes--> Simulator prints action
                        |no
                        v
                    Gemini generates a reply
                        -> Text-to-speech
                            -> Play through laptop speakers

Every interaction is logged to logs/YYYY-MM-DD.log
"""

import sys

from config import RECORD_SECONDS, VOICE_INPUT_PATH, RESPONSES_DIR
from audio.recorder import record, record_until_enter
from audio.player import play
from audio.audio_utils import unique_response_path
from ai.speech_to_text import transcribe
from ai.gemini_client import ask
from ai.text_to_speech import synthesize
from ai.conversation import log_interaction
from commands.parser import detect_command
from commands.simulator import execute_command
from commands.helmet_commands import NONE


def run_once(use_enter_to_stop: bool = False) -> None:
    """Runs a single record -> think -> respond cycle."""

    # 1. Record user speech
    if use_enter_to_stop:
        audio_path = record_until_enter(VOICE_INPUT_PATH)
    else:
        audio_path = record(RECORD_SECONDS, VOICE_INPUT_PATH)

    # 2. Speech -> text
    text = transcribe(audio_path)

    if not text:
        print("[Main] No speech detected. Try again.")
        return

    # 3. Check for a helmet command first (fast path, no API call)
    command = detect_command(text)

    if command != NONE:
        # 4a. Helmet command path
        response_text = execute_command(command)
        print(f"JARVIS: {response_text}")
        log_interaction(text, command, response_text)
        # Command confirmations are also spoken, for a consistent feel
        audio_reply = synthesize(response_text, unique_response_path(RESPONSES_DIR))
        play(audio_reply)

    else:
        # 4b. General conversation path
        reply = ask(text)
        print(f"JARVIS: {reply}")
        log_interaction(text, "NONE", reply)

        # 5. Text -> speech -> play
        audio_reply = synthesize(reply, unique_response_path(RESPONSES_DIR))
        play(audio_reply)


def main() -> None:
    print("=" * 50)
    print(" JARVIS AI Assistant — Phase 1 (Software Prototype)")
    print("=" * 50)
    print("Press Ctrl+C at any time to exit.\n")

    use_enter_mode = "--enter" in sys.argv

    while True:
        try:
            input("\nPress Enter, then speak...")
            run_once(use_enter_to_stop=use_enter_mode)
        except KeyboardInterrupt:
            print("\n[Main] Shutting down JARVIS. Goodbye.")
            break
        except Exception as e:
            print(f"[Main] Error: {e}")


if __name__ == "__main__":
    main()
