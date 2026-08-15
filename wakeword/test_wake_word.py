"""
wakeword/test_wake_word.py
------------------------------
Stand-alone test: just prints a message every time it hears
"Hey Jarvis". Run this FIRST, before touching main.py, to confirm
openWakeWord and your microphone are working together correctly.

Usage:
    python -m wakeword.test_wake_word
"""

from wakeword.listener import listen_for_wake_word

if __name__ == "__main__":
    print("Say 'Hey Jarvis' into your microphone. Press Ctrl+C to stop.\n")
    try:
        while True:
            listen_for_wake_word()
            print(">>> Wake word detected! (listening again...)\n")
    except KeyboardInterrupt:
        print("\nStopped.")
