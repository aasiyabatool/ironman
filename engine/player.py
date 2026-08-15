import os
import time
import subprocess

def play_audio(file_path, state=None):
    if not os.path.exists(file_path):
        print(f"Audio file not found: {file_path}")
        return

    if state:
        state.is_speaking.set()

    try:
        # Lock ALSA Master volume
        subprocess.run(["amixer", "set", "Master", "50%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Play response audio via ALSA
        subprocess.run(["aplay", file_path], check=True)
    except Exception as e:
        print(f"Error during audio playback: {e}")
    finally:
        # Acoustic reverberation cooldown before opening microphone
        time.sleep(0.4)
        if state:
            state.is_speaking.clear()
