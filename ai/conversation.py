"""
ai/conversation.py
--------------------
Logs every interaction (user text, detected action, and
JARVIS's response) to a daily log file inside logs/.
"""

import os
from datetime import datetime

from config import LOGS_DIR


def _log_path_for_today() -> str:
    filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    return os.path.join(LOGS_DIR, filename)


def log_interaction(user_text: str, action: str, response: str) -> None:
    """
    Appends one interaction to today's log file.

    Args:
        user_text: what the user said (recognized text).
        action: the detected helmet command, or "NONE".
        response: JARVIS's spoken/text response (or the
                  simulator's action confirmation).
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    entry = (
        f"[{timestamp}]\n"
        f"User: {user_text}\n"
        f"Action: {action}\n"
        f"Response: {response}\n"
        f"{'-' * 40}\n"
    )

    with open(_log_path_for_today(), "a", encoding="utf-8") as f:
        f.write(entry)
