"""
main.py
--------
Entry point for JARVIS -- now wake-word activated instead of
Enter-key activated.

Pipeline:

    Listen continuously for "Jarvis" (Porcupine)
        -> Record the command that follows
            -> Whisper speech-to-text
                -> Command parser
                    -> Helmet command?  --yes--> Simulator prints action
                            |no
                            v
                        Gemini generates a reply
                            -> Text-to-speech
                                -> Play through speakers

Every interaction is logged to logs/YYYY-MM-DD.log

Note: if you don't have Porcupine set up yet (or just want the old
keyboard-driven flow for quick testing), python test_text_mode.py
is unaffected by any of this -- it never used the microphone at all.
"""

import sys

from config import RECORD_SECONDS, VOICE_INPUT_PATH, RESPONSES_DIR
from wakeword.listener import listen_for_wake_word
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
    """Runs a single record -> think -> respond cycle, after the wake word fires."""

    # 1. Record the command that follows the wake word
    if use_enter_to_stop:
        audio_path = record_until_enter(VOICE_INPUT_PATH)
    else:
        audio_path = record(RECORD_SECONDS, VOICE_INPUT_PATH)

    # 2. Speech -> text
    text = transcribe(audio_path)

    if not text:
        print("[Main] No speech detected. Say the wake word to try again.")
        return

    # 3. Check for a helmet command first (fast path, no API call)
    command = detect_command(text)

    if command != NONE:
        # 4a. Helmet command path
        response_text = execute_command(command)
        print(f"JARVIS: {response_text}")
        log_interaction(text, command, response_text)
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
    print(" JARVIS AI Assistant — Wake-Word Activated")
    print("=" * 50)
    print("Say 'Hey Jarvis' at any time to start a command.")
    print("Press Ctrl+C to exit.\n")

    use_enter_mode = "--enter" in sys.argv

    while True:
        try:
            listen_for_wake_word()
            print("[Main] Listening for your command...")
            run_once(use_enter_to_stop=use_enter_mode)
        except KeyboardInterrupt:
            print("\n[Main] Shutting down JARVIS. Goodbye.")
            break
        except Exception as e:
            print(f"[Main] Error: {e}")


if __name__ == "__main__":
    main()
