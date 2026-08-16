import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are JARVIS, a concise, highly intelligent AI assistant inspired by Iron Man. Keep replies brief and conversational."
)

# ESP32 / Helmet Control Settings (Set to None if helmet hardware is offline)
esp32_env = os.getenv("ESP32_IP", "").strip()
ESP32_IP = esp32_env if esp32_env else None
ESP32_HTTP_PORT = int(os.getenv("ESP32_HTTP_PORT", "80"))
ESP32_REQUEST_TIMEOUT = float(os.getenv("ESP32_REQUEST_TIMEOUT", "0.5"))

# Audio / Voice Settings
TTS_ENGINE = os.getenv("TTS_ENGINE", "pyttsx3")
TTS_VOICE_GENDER = os.getenv("TTS_VOICE_GENDER", "male")
ROBOT_VOICE_EFFECT = os.getenv("ROBOT_VOICE_EFFECT", "false").lower() == "true"
TTS_SLOW = os.getenv("TTS_SLOW", "false").lower() == "true"

# Optimized Record Window (used as a fallback / by the fixed-length recorder)
RECORD_SECONDS = int(os.getenv("RECORD_SECONDS", "5"))

# How many trailing seconds of audio to snapshot for voice authentication
# when the wake word fires. This is a ROLLING buffer of what was just
# heard leading up to and including "Hey Jarvis" itself -- NOT audio
# recorded after the wake word. The user should say only "Hey Jarvis"
# and nothing else during authentication; that phrase alone is what
# gets analyzed.
AUTH_CLIP_SECONDS = float(os.getenv("AUTH_CLIP_SECONDS", "2.0"))

# Voice Activity Detection (auto-stop recording on silence)
USE_VAD_CAPTURE = os.getenv("USE_VAD_CAPTURE", "true").lower() == "true"
VAD_AGGRESSIVENESS = int(os.getenv("VAD_AGGRESSIVENESS", "2"))  # 0-3, higher = more aggressive filtering of non-speech
VAD_FRAME_MS = 20  # webrtcvad only accepts 10, 20, or 30ms frames
VAD_SILENCE_SECONDS = float(os.getenv("VAD_SILENCE_SECONDS", "1.0"))
VAD_MIN_RECORD_SECONDS = float(os.getenv("VAD_MIN_RECORD_SECONDS", "0.4"))
VAD_MAX_RECORD_SECONDS = float(os.getenv("VAD_MAX_RECORD_SECONDS", "8.0"))

# Whisper STT Settings
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base.en")

# Sensitivity Tuning
WAKE_WORD_THRESHOLD = 0.55
WAKE_WORD_THRESHOLD_WHILE_SPEAKING = 0.85

# Directory Paths
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
RESPONSES_DIR = os.path.join(BASE_DIR, "responses")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
VOICE_OUTPUT_PATH = os.path.join(RESPONSES_DIR, "jarvis_response.wav")

os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
