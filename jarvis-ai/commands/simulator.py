"""
commands/simulator.py
------------------------
Pretends to be the ESP32 + PCA9685 + servos + LEDs.

In Phase 2, execute_command() will be replaced with real
UART/Wi-Fi calls to the ESP32, e.g.:

    esp.send_command("OPEN_HELMET")

Every other module (recorder, whisper, parser, gemini, tts)
stays exactly the same. That's the whole point of this
architecture.
"""

from commands.helmet_commands import COMMAND_RESPONSES, NONE

from config import ESP32_IP, ESP32_HTTP_PORT, ESP32_REQUEST_TIMEOUT

# Maps our internal command constants to the ESP32's HTTP endpoints.
ENDPOINT_MAP = {
    "OPEN_HELMET": "open",
    "CLOSE_HELMET": "close",
    "LIGHTS_ON": "lights_on",
    "LIGHTS_OFF": "lights_off",
    "COMBAT_MODE": "combat",
    "PARTY_MODE": "party",
}


def _send_http_command(endpoint: str) -> bool:
    """
    Sends a GET request to the ESP32's HTTP endpoint. Returns True if
    it was received successfully, False otherwise (network issue,
    ESP32 offline, wrong IP, etc.) -- failures are logged but never
    crash the assistant, same as the old simulator's behavior.
    """
    url = f"http://{ESP32_IP}:{ESP32_HTTP_PORT}/{endpoint}"
    try:
        response = requests.get(url, timeout=ESP32_REQUEST_TIMEOUT)
        if response.status_code == 200:
            print(f"[ESP32] Sent: {endpoint} -> {response.text}")
            return True
        else:
            print(f"[ESP32] Unexpected response ({response.status_code}) for {endpoint}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ESP32] Could not reach {url}: {e}")
        return False



def execute_command(command: str) -> str:
    """
    "Executes" a helmet command by printing what would
    physically happen on the real hardware.

    Args:
        command: one of the command constants from helmet_commands.py

    Returns:
        A human-readable confirmation string, e.g. "Opening helmet."
    """
    if command == NONE:
        return ""

    message = COMMAND_RESPONSES.get(command, f"Executing {command}.")
    print(f"[Simulator] >>> {message}")
    return message


# ---------------------------------------------------------------
# Status LED helpers -- call these directly from main.py at the
# right points in the voice pipeline so the eyes reflect what
# JARVIS is actually doing (listening / thinking / speaking /
# ready / error). These bypass the command parser entirely since
# they're triggered by pipeline state, not spoken commands.
# ---------------------------------------------------------------

def set_listening() -> None:
    _send_http_command("listening")


def set_thinking() -> None:
    _send_http_command("thinking")


def set_speaking() -> None:
    _send_http_command("speaking")


def set_ready() -> None:
    _send_http_command("ready")


def set_error() -> None:
    _send_http_command("error")
