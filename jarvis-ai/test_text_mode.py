"""
test_text_mode.py
--------------------
A lightweight way to test the JARVIS pipeline WITHOUT a
microphone. Useful for verifying your Gemini API key, the
command parser, and text-to-speech before dealing with any
audio recording setup.

Usage:
    python test_text_mode.py
    You: open helmet
    You: who built you?
    You: exit
"""

from ai.gemini_client import ask
from ai.text_to_speech import synthesize
from ai.conversation import log_interaction
from audio.player import play
from audio.audio_utils import unique_response_path
from commands.parser import detect_command
from commands.simulator import execute_command
from commands.helmet_commands import NONE
from config import RESPONSES_DIR


def main():
    print("JARVIS text-mode test. Type 'exit' to quit.\n")

    while True:
        text = input("You: ").strip()
        if text.lower() in ("exit", "quit"):
            print("JARVIS: Powering down. Goodbye.")
            break

        if not text:
            continue

        command = detect_command(text)

        if command != NONE:
            response = execute_command(command)
        else:
            response = ask(text)

        print(f"JARVIS: {response}\n")
        log_interaction(text, command, response)

        try:
            output_path = unique_response_path(RESPONSES_DIR)
            audio_path = synthesize(response, output_path)
            play(audio_path)
        except Exception as e:
            print(f"[TTS/Player skipped: {e}]")


if __name__ == "__main__":
    main()
