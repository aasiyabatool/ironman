"""
audio/player.py
----------------
Handles ONLY audio playback. Uses system players (mpg123 for mp3,
aplay for wav) via subprocess instead of the `playsound` package,
which is unreliable on headless Linux/Raspberry Pi OS. Applies an
optional volume boost via ffmpeg before playback.
"""

import subprocess
import shutil

VOLUME_MULTIPLIER = 20
.0  # start here, raise carefully if it's not distorting


def play(file_path: str) -> None:
    """
    Plays an audio file (.wav or .mp3) through the system's
    default output device (the MAX98357A speaker on the helmet).
    """
    print(f"[Player] Playing {file_path}")

    boosted_path = file_path + ".boosted.wav"
    play_path = file_path
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", file_path, "-af", f"volume={VOLUME_MULTIPLIER}", boosted_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        play_path = boosted_path
    except subprocess.CalledProcessError:
        pass  # fall back to the original file if the boost step fails

    if play_path.lower().endswith(".mp3"):
        player, args = "mpg123", ["-q", play_path]
    else:
        player, args = "aplay", [play_path]

    if shutil.which(player) is None:
        print(f"[Player] '{player}' not found. Install it with: sudo apt install {player}")
        return

    try:
        subprocess.run([player, *args], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Player] Could not play audio: {e}")
