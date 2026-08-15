# JARVIS AI — Phase 1 (Software Prototype)

A fully working, hardware-free AI voice assistant built to be the software
foundation of the Iron Man helmet project. This is Phase 1: everything runs
on your laptop using its microphone and speakers. Once this works, Phase 2
swaps in the ESP32-S3 hardware with changes to only **one file**
(`commands/simulator.py` → a real ESP32 client).

---

## 1. What this does

```
You speak into your laptop mic
        ↓
Whisper converts speech → text
        ↓
Parser checks: is this a helmet command?
        ↓                           ↓
      Yes                          No
        ↓                           ↓
  Simulator prints              Gemini generates
  "Opening Helmet..."           a JARVIS-style reply
        ↓                           ↓
        └────────────┬──────────────┘
                      ↓
              Text-to-Speech
                      ↓
           Played through your speakers
                      ↓
          Logged to logs/YYYY-MM-DD.log
```

---

## 2. Folder structure

```
jarvis-ai/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py                  # full voice pipeline (mic in, speech out)
├── test_text_mode.py         # type instead of speak — good for first test
├── config.py                 # all settings live here
│
├── audio/
│   ├── recorder.py           # records from laptop mic
│   ├── player.py              # plays audio replies
│   └── audio_utils.py
│
├── ai/
│   ├── speech_to_text.py       # Whisper
│   ├── gemini_client.py         # Gemini API + JARVIS personality
│   ├── text_to_speech.py         # gTTS / pyttsx3
│   └── conversation.py            # logging
│
├── commands/
│   ├── parser.py               # detects "open helmet" etc. in text
│   ├── helmet_commands.py       # command definitions & phrases
│   └── simulator.py              # stands in for the ESP32 for now
│
├── models/       # Whisper model cache lands here
├── recordings/   # your recorded voice.wav files
├── responses/    # generated reply.mp3 files
├── temp/
├── logs/         # one log file per day
└── docs/
```

---

## 3. Prerequisites

- Python 3.10 or 3.11 (Whisper + torch are most stable on these versions)
- `ffmpeg` installed and on your PATH (required by Whisper)
- A free **Gemini API key** from https://aistudio.google.com/apikey

### Install ffmpeg

- **Windows:** `winget install ffmpeg` (or download from ffmpeg.org and add to PATH)
- **macOS:** `brew install ffmpeg portaudio`
- **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg portaudio19-dev`

---

## 4. Setup

```bash
# 1. Clone / unzip the project, then move into it
cd jarvis-ai

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up your environment file
cp .env.example .env
# then open .env and paste in your real GEMINI_API_KEY
```

> **Note on Whisper:** the first time you run the app, Whisper will download
> its model weights automatically (a few hundred MB for the `base` model).
> This requires an internet connection once, then works offline afterward.

---

## 5. Running it

### Step A — Test without a microphone first (recommended)

This verifies your Gemini key, the command parser, and text-to-speech all
work before you deal with any audio recording setup:

```bash
python test_text_mode.py
```

```
You: open helmet
JARVIS: Opening helmet.

You: who built you?
JARVIS: I am the onboard AI assistant designed to assist with
navigation, information, and helmet control.

You: exit
```

### Step B — Full voice pipeline

```bash
python main.py
```

- Press **Enter**, then speak. It records for `RECORD_SECONDS` (default 5,
  configurable in `.env`).
- Whisper transcribes what you said.
- If it matches a helmet command ("open helmet", "close helmet",
  "lights on", "lights off"), the simulator prints the action and speaks
  a confirmation.
- Otherwise, Gemini answers in character as JARVIS, and the reply is
  spoken back to you.
- Press **Ctrl+C** to exit.

### Optional: press-Enter-to-stop recording mode

Instead of a fixed 5-second window, you can start recording immediately
and press Enter again when you're done talking:

```bash
python main.py --enter
```

---

## 6. Customizing JARVIS

- **Change how JARVIS addresses you:** edit `ASSISTANT_TITLE` in `.env`
  (`Sir` or `Ma'am`).
- **Change the personality/prompt:** edit `SYSTEM_PROMPT` in `config.py`.
- **Add new helmet commands:** add phrases to `commands/helmet_commands.py`
  — no changes needed in `parser.py` or `main.py`.
- **Switch to fully offline TTS:** set `TTS_ENGINE=pyttsx3` in `.env`
  (no internet needed, but more robotic-sounding voice).
- **Speed up Whisper:** set `WHISPER_MODEL_SIZE=tiny` in `.env` for faster,
  slightly less accurate transcription — good for quick testing.

---

## 7. Checking your logs

Every interaction (what you said, which command fired, and what JARVIS
replied) is appended to a daily log file:

```
logs/2026-07-15.log
```

```
[14:32:10]
User: open helmet
Action: OPEN_HELMET
Response: Opening helmet.
----------------------------------------
```

---

## 8. What's next (Phase 2 preview)

Right now, `commands/simulator.py` just prints what the helmet *would* do.
When you move to the ESP32-S3 hardware, you'll replace only this:

```python
# Today (simulator.py)
print("Opening Helmet...")
```

```python
# Later (Phase 2, e.g. an esp32_client.py)
esp.send_command("OPEN_HELMET")   # sent over UART or Wi-Fi
```

Everything else — Whisper, the parser, Gemini, and text-to-speech — stays
exactly the same. That's the entire point of keeping these modules
independent from the start.

---

## 9. Troubleshooting

| Problem | Likely fix |
|---|---|
| `GEMINI_API_KEY is not set` | Make sure you copied `.env.example` to `.env` and filled in your key |
| Whisper import error | Make sure `ffmpeg` is installed and on PATH |
| No sound plays | Check `TTS_ENGINE` in `.env`; try switching between `gtts` and `pyttsx3` |
| `sounddevice`/`portaudio` install error | Install `portaudio` first (see Prerequisites), then re-run `pip install -r requirements.txt` |
| Recording is silent / empty | Check your OS microphone permissions for the terminal/IDE you're using |
