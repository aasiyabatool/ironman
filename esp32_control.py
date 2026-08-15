"""
esp32_control.py
Sends HTTP commands from the Raspberry Pi to the ESP32 helmet controller.
Plug this into jarvis-ai's command handler so voice commands trigger
the mask/eyes/lights over WiFi.
"""

import requests

# Set this to the IP address printed in the ESP32's Serial Monitor
# on boot (e.g. "Connecting to WiFi... WiFi connected! IP address: 192.168.1.42")
ESP32_IP = "192.168.137.145"   # <-- change this to your ESP32's actual IP
BASE_URL = f"http://{ESP32_IP}"
TIMEOUT = 3  # seconds


def _send(endpoint: str) -> bool:
    """Send a GET request to one of the ESP32's HTTP endpoints."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        print(f"[ESP32] {endpoint} -> {resp.status_code} {resp.text}")
        return resp.ok
    except requests.exceptions.RequestException as e:
        print(f"[ESP32] Failed to reach {url}: {e}")
        return False


# ---- Wrapper functions matching the ESP32's endpoints ----
def open_helmet():
    return _send("open")

def close_helmet():
    return _send("close")

def lights_on():
    return _send("lights_on")

def lights_off():
    return _send("lights_off")

def combat_mode():
    return _send("combat_mode")

def party_mode():
    return _send("party_mode")

def normal_mode():
    return _send("normal_mode")

def status_listening():
    return _send("status_listening")

def status_ready():
    return _send("status_ready")

def status_processing():
    return _send("status_processing")

def status_error():
    return _send("status_error")

def get_status():
    """Returns 'OPEN' or 'CLOSED', or None if unreachable."""
    try:
        resp = requests.get(f"{BASE_URL}/status", timeout=TIMEOUT)
        return resp.text.strip()
    except requests.exceptions.RequestException:
        return None


# ---- Simple command matcher for voice transcripts ----
# Call this with the text Whisper returns after transcription.
VOICE_COMMANDS = {
    "open helmet": open_helmet,
    "open mask": open_helmet,
    "close helmet": close_helmet,
    "close mask": close_helmet,
    "lights on": lights_on,
    "lights off": lights_off,
    "combat mode": combat_mode,
    "party mode": party_mode,
    "normal mode": normal_mode,
}


def handle_voice_command(transcript: str) -> bool:
    """
    Checks a lowercased transcript for a known phrase and fires the
    matching ESP32 action. Returns True if a command was matched and sent.
    """
    text = transcript.lower().strip()
    for phrase, action in VOICE_COMMANDS.items():
        if phrase in text:
            print(f"[Voice] Matched '{phrase}'")
            action()
            return True
    return False


if __name__ == "__main__":
    # Quick manual test: run this file directly on the Pi to check
    # connectivity before wiring it into jarvis-ai.
    print("Current status:", get_status())
    print("Sending open command...")
    open_helmet()