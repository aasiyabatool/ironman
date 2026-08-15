"""
ai/gemini_client.py
---------------------
Wraps all calls to Google's Gemini API. Keeps JARVIS's
personality and conversation history isolated from the
rest of the pipeline.
"""

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT

_chat_session = None


def _get_chat_session():
    """
    Lazily creates a single ongoing chat session so JARVIS
    remembers context across turns within one run of the program.
    """
    global _chat_session

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to your .env file. "
            "See .env.example for the expected format."
        )

    if _chat_session is None:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        _chat_session = model.start_chat(history=[])

    return _chat_session


def ask(text: str) -> str:
    """
    Sends user text to Gemini and returns JARVIS's reply.

    Args:
        text: the recognized user speech.

    Returns:
        JARVIS's text response.
    """
    chat = _get_chat_session()
    print("[Gemini] Thinking...")
    response = chat.send_message(text, generation_config={"max_output_tokens": 120})
    reply = response.text.strip()
    print(f"[Gemini] Reply: \"{reply}\"")
    return reply


def reset_conversation() -> None:
    """Clears the chat history, starting a fresh conversation."""
    global _chat_session
    _chat_session = None
