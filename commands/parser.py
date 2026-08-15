"""
commands/parser.py
---------------------
Detects whether recognized speech contains a helmet command.
This is deliberately rule-based (not AI-based) so command
execution is fast, deterministic, and doesn't depend on an
API call. Gemini is only used for open-ended conversation.
"""

from commands.helmet_commands import COMMAND_PHRASES, NONE, OPEN_HELMET, CLOSE_HELMET

# Fuzzy fallback word sets -- faster-whisper on the Pi mic regularly
# clips "helmet" down to "head" ("close helmet" -> "close head"), so
# the exact phrase list in helmet_commands.py misses it and the
# command silently falls through to Gemini, which just role-plays a
# response without ever calling execute_command(). Catching
# action-word + target-word combos separately fixes that.
OPEN_ACTION_WORDS = {"open", "raise", "lift", "unseal"}
CLOSE_ACTION_WORDS = {"close", "lower", "seal", "shut", "drop"}
HELMET_TARGET_WORDS = {"helmet", "head", "faceplate", "face", "plate", "mask", "visor"}


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

    words = set(normalized.replace(".", "").split())
    if words & HELMET_TARGET_WORDS:
        if words & CLOSE_ACTION_WORDS:
            return CLOSE_HELMET
        if words & OPEN_ACTION_WORDS:
            return OPEN_HELMET

    return NONE
