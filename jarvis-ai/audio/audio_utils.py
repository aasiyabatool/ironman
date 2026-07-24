"""
audio/audio_utils.py
---------------------
Small shared helpers used by recorder.py and player.py.
Kept separate so audio-format logic doesn't leak into
the rest of the codebase.
"""

import os
import time
import uuid


def file_exists(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def cleanup_temp_files(*paths: str) -> None:
    """Deletes temporary audio files after they're no longer needed."""
    for path in paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass


def unique_response_path(directory: str, extension: str = ".mp3") -> str:
    """
    Builds a unique file path inside `directory` for each spoken reply.

    On Windows, playback libraries like playsound sometimes keep a file
    handle open briefly after playback finishes. Reusing the exact same
    output filename on the very next turn can then raise a
    "PermissionError: [Errno 13]" when the TTS engine tries to overwrite
    it. Writing each reply to a fresh, uniquely-named file avoids that
    entirely.
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"reply_{timestamp}_{unique_id}{extension}"
    return os.path.join(directory, filename)
