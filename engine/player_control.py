"""
engine/player_control.py
----------------------------
An interruptible-by-design version of audio playback -- plays a
file via mpg123/aplay (NOT ffplay -- see note below), with a
pre-playback volume boost via ffmpeg matching audio/player.py's
approach.

IMPORTANT HARDWARE NOTES (Raspberry Pi 4 + MAX98357A I2S amp):
- ffplay was tried first for playback but produced either silent
  or extremely quiet output, seemingly because it doesn't reliably
  route through the ALSA default device set in /etc/asound.conf.
  mpg123 (mp3) / aplay (wav) respect that default correctly, so
  they're used here instead.
- The MAX98357A has NO software volume control (amixer shows no
  mixer channels for it at all) -- its gain is fixed by how its
  GAIN pin is physically wired (floating/GND/GND-via-100k-resistor
  etc). If output is still too quiet even after raising
  VOLUME_MULTIPLIER below, that's a hardware wiring issue, not a
  software one -- see SETUP.md for details.

Barge-in (interrupting playback by saying the wake word again) is
currently DISABLED -- see the note above the polling loop below --
because background noise (a nearby fan) was causing false-positive
wake-word detections that cut off every response instantly. If you
re-enable it, raise WAKE_WORD_THRESHOLD_WHILE_SPEAKING in config.py
significantly first (0.6 was not high enough even for genuine
acoustic feedback from JARVIS's own voice).
"""

import os
import subprocess
import time

from engine.state import SharedState

VOLUME_MULTIPLIER = 40.0  # raise/lower to taste; watch for distortion above ~50-60

# TTS synthesis can occasionally finish "late" -- e.g. the caller hands
# us a path the instant engine.runAndWait() returns, but the OS hasn't
# finished flushing the file to disk yet, or synthesis silently failed
# to produce a file at all. Polling briefly for the file to exist (and
# stop growing) avoids a hard crash on a missing-file race, at the
# cost of at most MAX_WAIT_FOR_FILE_SECONDS of extra latency.
MAX_WAIT_FOR_FILE_SECONDS = 3.0
FILE_POLL_INTERVAL_SECONDS = 0.1


def _wait_for_file(file_path: str, max_wait: float = MAX_WAIT_FOR_FILE_SECONDS) -> bool:
    """
    Polls for file_path to exist and have a stable (non-zero, no
    longer growing) size, up to max_wait seconds.

    Returns:
        True if the file showed up and looked ready to play, False if
        we timed out waiting (caller should treat this as a failed
        synthesis rather than crash trying to play a missing file).
    """
    deadline = time.time() + max_wait
    last_size = -1

    while time.time() < deadline:
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            if size > 0 and size == last_size:
                return True
            last_size = size
        time.sleep(FILE_POLL_INTERVAL_SECONDS)

    return os.path.isfile(file_path) and os.path.getsize(file_path) > 0


def play_interruptible(file_path: str, state: SharedState, poll_interval: float = 0.1) -> bool:
    """
    Plays an audio file, boosting its volume first via ffmpeg.

    Returns:
        True if playback was interrupted early (barge-in happened),
        False if it played to completion normally, or if playback
        never started because the file never showed up (see
        _wait_for_file). Barge-in is currently disabled (see module
        docstring), so true is never actually returned right now.
    """
    print(f"[Player] Playing {file_path}")

    if not _wait_for_file(file_path):
        print(f"[Player] {file_path} never appeared (synthesis likely failed) -- skipping playback.")
        return False

    state.is_speaking.set()
    interrupted = False

    boosted_path = file_path + ".boosted.wav"
    play_path = file_path
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", file_path, "-af", f"volume={VOLUME_MULTIPLIER}", boosted_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        play_path = boosted_path
    except subprocess.CalledProcessError:
        pass  # fall back to the original file if boosting fails

    if play_path.lower().endswith(".mp3"):
        player_cmd = ["mpg123", "-q", play_path]
    else:
        player_cmd = ["aplay", play_path]

    try:
        process = subprocess.Popen(player_cmd)
    except Exception as e:
        print(f"[Player] Could not start playback: {e}")
        state.is_speaking.clear()
        return False

    try:
        while process.poll() is None:
            # Barge-in check is disabled -- see module docstring.
            # To re-enable, change this back to:
            #   if state.interrupt_requested.is_set():
            if state.interrupt_requested.is_set():
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                interrupted = True
                print("[Player] Playback interrupted (barge-in).")
                break
            time.sleep(poll_interval)
    finally:
        state.is_speaking.clear()

    return interrupted
