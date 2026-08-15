"""
commands/parser.py
---------------------
Detects whether recognized speech contains a helmet command.
This is deliberately rule-based (not AI-based) so command
execution is fast, deterministic, and doesn't depend on an
API call. Gemini is only used for open-ended conversation.
"""

from commands.helmet_commands import COMMAND_PHRASES, NONE


def detect_command(text: str) -> str:
    """
    Checks recognized text against known helmet command phrases.

    Args:
        text: recognized user speech.

    Returns:
        One of the command constants (e.g. "OPEN_HELMET"),
        or "NONE" if no command matched.
    """
    normalized = text.lower().strip()

    for command, phrases in COMMAND_PHRASES.items():
        for phrase in phrases:
            if phrase in normalized:
                return command

    return NONE
