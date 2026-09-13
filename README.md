# JARVIS — Iron Man AI Smart Helmet

An always-listening, voice-controlled AI assistant for a real, wearable Iron Man-style helmet — built during our internship at PI Lab, FAST-NUCES. Say "Hey Jarvis," and it wakes up, verifies it's actually you talking, runs your command (open the mask, lights on, switch modes...), or just chats back in character. It also recognizes faces through the built-in camera and greets people by name.

---

## What it actually does

```
"Hey Jarvis" spoken aloud
        ↓
openWakeWord detects the wake phrase (fully offline, no API key)
        ↓
A short audio clip is checked against enrolled voiceprints
        ↓                                   ↓
  Recognized speaker                   Unknown speaker
        ↓                                   ↓
  Command is transcribed              Request ignored
  (faster-whisper) and                (helmet stays silent
  classified as a helmet                to unauthorized voices)
  command or free chat
        ↓                           ↓
  Sent to the ESP32 over        Gemini replies
  Wi-Fi (mask, lights,          in JARVIS's voice
  LED modes, status LEDs)
        ↓                           ↓
        └───────────┬───────────────┘
                     ↓
         Text-to-speech (pyttsx3), interruptible —
         say "Hey Jarvis" again to talk over it
                     ↓
          Logged to logs/YYYY-MM-DD.log
```

Meanwhile, a second thread watches the camera continuously and greets recognized faces by name (`main_combined.py`), sharing the same speaker as the voice pipeline without talking over it.

---

## Hardware

- **Raspberry Pi** — runs the full voice + vision pipeline
- **ESP32** — drives the helmet's mask servo, LEDs, and status indicators, controlled over Wi-Fi/HTTP
- **I2S audio**: Google VoiceHAT, INMP441 mic, MAX98357A amp

## Core modules

| Module | What it's for |
|---|---|
| `wakeword/` | Always-on "Hey Jarvis" detection using openWakeWord |
| `voice_auth/` | Enrolls speakers and verifies identity with a multi-class SVM before any command is accepted |
| `ai/speech_to_text.py` | Transcription via faster-whisper (int8, CPU-only, ARM-friendly) |
| `intent_classifier/` | Classifies transcribed text into a specific helmet command |
| `ai/gemini_client.py` | Free-form JARVIS-style conversation for anything that isn't a command |
| `ai/text_to_speech.py` | pyttsx3 (offline default) or gTTS, interruptible playback |
| `vision/` | Face enrollment + live recognition and greeting via the camera |
| `esp32_control.py` | Sends the actual open/close/lights/mode commands to the ESP32 over HTTP |
| `commands/` | Parses text into command intents and simulates/executes them |
| `engine/` | Shared state, threading, and interruptible audio playback |

## Try it yourself

```bash
git clone <this repo>
cd ironman
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY
```

Enroll your voice and face first:

```bash
python -m voice_auth.enroll
python vision/enroll_face.py
```

Then run the full experience (wake word + commands + face greetings, all at once):

```bash
python main_combined.py
```

Or just the voice pipeline on its own:

```bash
python main.py
```

No hardware handy? `python test_text_mode.py` lets you type instead of speak, so you can test the parser, voice auth stub, and Gemini replies without a mic or an ESP32.

See `requirements.txt` for platform-specific notes (Pi vs. Windows vs. macOS) — a few packages (scipy, openwakeword, opencv-contrib) need exact versions or system-level installs to behave on ARM.

---

Built by Laiba and [Aasiya Batool](https://github.com/aasiyabatool) at PI Lab, FAST-NUCES.
