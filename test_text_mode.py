"""
test_text_mode.py
--------------------
A lightweight way to test the JARVIS pipeline WITHOUT a
microphone.

Combat Mode and Party Mode are treated as PERSISTENT states: once
activated, the status LED auto-update (processing -> ready) is
skipped for these two specific commands, so they stay red/rainbow
until you explicitly say "normal mode" (or another command that
changes the LEDs, like "lights off").

Usage:
    python test_text_mode.py
    You: combat mode      (stays red)
    You: party mode       (rainbow loops until stopped)
    You: normal mode      (cancels either one)
    You: exit
"""

from ai.gemini_client import ask
from ai.text_to_speech import synthesize
from ai.conversation import log_interaction
from audio.player import play
from commands.parser import detect_command
from commands.simulator import execute_command
from commands.helmet_commands import NONE, COMBAT_MODE, PARTY_MODE
from commands.status_led import set_status
from config import VOICE_OUTPUT_PATH

# Commands that intentionally leave the LEDs in a persistent state --
# the automatic "back to ready" status update is skipped for these.
PERSISTENT_LED_COMMANDS = {COMBAT_MODE, PARTY_MODE}


def main():
    print("JARVIS text-mode test. Type 'exit' to quit.\n")
    set_status("ready")

    while True:
        text = input("You: ").strip()
        if text.lower() in ("exit", "quit"):
            print("JARVIS: Powering down. Goodbye.")
            break

        if not text:
            continue

        set_status("processing")

        try:
            command = detect_command(text)

            if command != NONE:
                response = execute_command(command)
            else:
                response = ask(text)

            print(f"JARVIS: {response}\n")
            log_interaction(text, command, response)

            try:
                audio_path = synthesize(response, VOICE_OUTPUT_PATH)
                play(audio_path)
            except Exception as e:
                print(f"[TTS/Player skipped: {e}]")

            # Only snap back to "ready" (green) if this command
            # didn't intentionally set a persistent LED state.
            if command not in PERSISTENT_LED_COMMANDS:
                set_status("ready")

        except Exception as e:
            print(f"[Main] Error: {e}")
            set_status("error")


if __name__ == "__main__":
    main()
