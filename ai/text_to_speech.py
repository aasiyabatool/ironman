"""
ai/text_to_speech.py
----------------------
Converts JARVIS's text reply into a spoken audio file.

Two engines are supported:
  - "gtts"     : Google Text-to-Speech, natural sounding, needs internet.
                 Only one voice per language (no gender selection).
  - "pyttsx3"  : Fully offline, uses your OS's installed voices, and lets
                 us actually pick a male voice.

On top of either engine, a JARVIS-style robotic effect (pitch-shifted
down + a subtle mechanical warble) can be applied via ffmpeg. This is
controlled by ROBOT_VOICE_EFFECT in config.py / .env.
"""

import os
import subprocess

# CHANGE 1: Add TTS_SLOW to imports
from config import TTS_ENGINE, TTS_VOICE_GENDER, ROBOT_VOICE_EFFECT, TTS_SLOW, VOICE_OUTPUT_PATH

# A single, persistent pyttsx3 engine instance, created once and reused
# for every synthesize() call. pyttsx3 wraps its platform driver
# (e.g. espeak on Linux) in objects that pyttsx3.init() sets up with
# weak references; creating a fresh engine per call and letting the
# local variable go out of scope mid-synthesis caused intermittent
# `ReferenceError`s on Python 3.13 when the driver object got garbage
# collected before runAndWait() finished. Keeping one module-level
# engine alive for the process lifetime avoids that entirely.
_pyttsx3_engine = None


def _get_pyttsx3_engine():
    global _pyttsx3_engine
    if _pyttsx3_engine is None:
        import pyttsx3

        _pyttsx3_engine = pyttsx3.init()
        _pyttsx3_engine.setProperty("rate", 155)
        _select_voice(_pyttsx3_engine, TTS_VOICE_GENDER)
    return _pyttsx3_engine

def synthesize(text: str, output_path: str = VOICE_OUTPUT_PATH) -> str:
    """
    Converts text into speech and saves it to output_path.
    If ROBOT_VOICE_EFFECT is enabled, a second, processed file is
    created and its path is returned instead.

    Returns:
        The path to the final generated audio file.
    """
    print("[TTS] Generating speech...")

    if TTS_ENGINE == "gtts":
        _synthesize_gtts(text, output_path)
        raw_path = output_path
    else:
        raw_path = _synthesize_pyttsx3(text, output_path)

    if ROBOT_VOICE_EFFECT:
        final_path = _apply_robot_voice_effect(raw_path)
        print(f"[TTS] Applied robotic voice effect -> {final_path}")
        return final_path

    print(f"[TTS] Saved audio to {raw_path}")
    return raw_path


# CHANGE 2: Pass slow parameter to gTTS
def _synthesize_gtts(text: str, output_path: str) -> None:
    from gtts import gTTS

    tts = gTTS(text=text, lang="en", slow=TTS_SLOW)
    tts.save(output_path)


def _synthesize_pyttsx3(text: str, output_path: str) -> str:
    if not output_path.endswith(".wav"):
        output_path = output_path.rsplit(".", 1)[0] + ".wav"

    # Reuse the one persistent engine instead of creating (and
    # discarding) a new one on every call -- see _get_pyttsx3_engine().
    engine = _get_pyttsx3_engine()
    engine.save_to_file(text, output_path)
    engine.runAndWait()

    return output_path

def _select_voice(engine, gender_preference: str) -> None:
    """
    Attempts to select a voice matching the requested gender.
    Falls back to the first available voice if no clear match is found
    (this happens on some Linux/espeak setups where voices aren't
    labeled by gender at all).
    """
    voices = engine.getProperty("voices")
    if not voices:
        return

    preference = gender_preference.lower()

    # Common male voice identifiers across Windows (SAPI5), macOS, and
    # some espeak configurations.
    male_hints = ("male", "david", "alex", "mark", "daniel", "fred", "george")
    female_hints = ("female", "zira", "samantha", "victoria", "susan", "karen")

    hints = male_hints if preference == "male" else female_hints

    for voice in voices:
        name = (voice.name or "").lower()
        voice_id = (voice.id or "").lower()
        gender_attr = str(getattr(voice, "gender", "") or "").lower()

        if any(hint in name or hint in voice_id or hint in gender_attr for hint in hints):
            engine.setProperty("voice", voice.id)
            return

    # No clear match — use whatever the system offers first.
    engine.setProperty("voice", voices[0].id)


def _apply_robot_voice_effect(input_path: str) -> str:
    """
    Applies a deep Iron Man / JARVIS helmet effect using ffmpeg:
      1. Pitch down significantly (asetrate = 44100 * 0.75 for a deep bass tone)
      2. Normalize sample rate back to 44100
      3. Apply a lowpass filter to mimic speaking through a suit helmet
      4. Bass boost to give it weight
    """
    base, _ext = os.path.splitext(input_path)
    output_path = f"{base}_robot.mp3"

    # asetrate at 0.72 - 0.78 gives a deep, villain/helmet bass tone without turning into static
    filter_chain = (
        "asetrate=44100*0.75,"      # Pitch down ~25% (makes voice much deeper and naturally slower)
        "aresample=44100,"         # Fix sample rate
        "equalizer=f=100:width_type=h:width=200:g=6," # Boost bass frequencies for resonance
        "lowpass=f=4000"           # Subtle helmet/mic enclosure effect (cuts high-end harshness)
    )

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-af", filter_chain, output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[TTS] Robot voice effect failed ({e}); using unprocessed audio instead.")
        return input_path