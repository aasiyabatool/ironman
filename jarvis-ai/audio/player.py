"""
audio/player.py
----------------
Handles ONLY audio playback. Later this will be replaced with
code that streams audio to the MAX98357A amplifier + speaker
on the helmet, but nothing else in the pipeline will change.
"""

from playsound import playsound


def play(file_path: str) -> None:
    """
    Plays an audio file (.wav or .mp3) through the system's
    default output device.
    """
    print(f"[Player] Playing {file_path}")
    try:
        playsound(file_path)
    except Exception as e:
        print(f"[Player] Could not play audio: {e}")
