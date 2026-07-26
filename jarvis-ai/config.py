"""
config.py
---------
Central configuration for the JARVIS AI assistant.
All other modules pull their settings from here so nothing
is hardcoded in multiple places.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# API Keys
# ----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ----------------------------
# Gemini Model Settings
# ----------------------------
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# ----------------------------
# Whisper Settings
# ----------------------------
# tiny | base | small | medium | large
# "tiny" or "base" is recommended for fast laptop testing.
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# ----------------------------
# Audio Settings
# ----------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = int(os.getenv("RECORD_SECONDS", "5"))

# ----------------------------
# Text-to-Speech Settings
# ----------------------------
TTS_SLOW = False
# "gtts" (online, natural) or "pyttsx3" (offline, robotic but no internet needed)
TTS_ENGINE = os.getenv("TTS_ENGINE", "gtts")

ASSISTANT_TITLE = os.getenv("ASSISTANT_TITLE", "Sir")  # "Sir" or "Ma'am"

# Preferred voice gender when using pyttsx3 (has no effect on gTTS, which
# only offers one voice per language). "male" or "female".
TTS_VOICE_GENDER = os.getenv("TTS_VOICE_GENDER", "male")

# Applies a JARVIS-style pitch-shift + robotic modulation to every spoken
# reply, regardless of which TTS engine generated it. Requires ffmpeg
# (already a dependency for Whisper, so nothing extra to install).
ROBOT_VOICE_EFFECT = os.getenv("ROBOT_VOICE_EFFECT", "true").lower() == "true"

# ----------------------------
# Wake Word Settings (openWakeWord)
# ----------------------------
# openWakeWord is fully local and free -- no account or API key
# needed. Its pretrained model listens for the phrase "Hey Jarvis"
# specifically (bare "Jarvis" may also trigger it, but less reliably).
#
# WAKE_WORD_THRESHOLD is a score from 0-1: how confident the model
# needs to be before triggering. Lower = more sensitive (may
# false-trigger more often); higher = stricter (may miss you
# occasionally). 0.5 is openWakeWord's own recommended default.
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))

# ----------------------------
# File Paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
RESPONSES_DIR = os.path.join(BASE_DIR, "responses")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

VOICE_INPUT_PATH = os.path.join(RECORDINGS_DIR, "voice.wav")
VOICE_OUTPUT_PATH = os.path.join(RESPONSES_DIR, "reply.mp3")

# Make sure required folders exist
for folder in (RECORDINGS_DIR, RESPONSES_DIR, TEMP_DIR, LOGS_DIR):
    os.makedirs(folder, exist_ok=True)

# ----------------------------
# JARVIS System Prompt
# ----------------------------
SYSTEM_PROMPT = f"""You are JARVIS, the AI assistant integrated into an Iron Man inspired robotic helmet.

Your personality should be calm, intelligent, concise and professional.

Never mention that you are Gemini, ChatGPT, or any underlying language model.

Respond as if you are the onboard assistant inside the helmet.

When the user asks a general question, answer naturally.

When the user issues a helmet control command such as:
- Open Helmet
- Close Helmet
- Lights On
- Lights Off

do NOT describe the action. These commands are intercepted before reaching you,
so you will never actually be asked to handle them directly.

Responses should usually be under 3 sentences unless asked for detail.

Refer to the user as "{ASSISTANT_TITLE}".

Never explain that you are an AI language model.

Stay in character at all times.
"""
