"""
commands/simulator.py
------------------------
Pretends to be the ESP32 + PCA9685 + servos + LEDs.

In Phase 2, execute_command() will be replaced with real
UART/Wi-Fi calls to the ESP32, e.g.:

    esp.send_command("OPEN_HELMET")

Every other module (recorder, whisper, parser, gemini, tts)
stays exactly the same. That's the whole point of this
architecture.
"""

from commands.helmet_commands import COMMAND_RESPONSES, NONE


def execute_command(command: str) -> str:
    """
    "Executes" a helmet command by printing what would
    physically happen on the real hardware.

    Args:
        command: one of the command constants from helmet_commands.py

    Returns:
        A human-readable confirmation string, e.g. "Opening helmet."
    """
    if command == NONE:
        return ""

    message = COMMAND_RESPONSES.get(command, f"Executing {command}.")
    print(f"[Simulator] >>> {message}")
    return message
