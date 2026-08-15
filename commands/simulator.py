"""
commands/simulator.py
------------------------
Sends helmet commands to the REAL ESP32 over WiFi (HTTP).

The HTTP request is fired in a background thread so this function
returns immediately -- letting JARVIS start generating and playing
its spoken reply (TTS) AT THE SAME TIME the ESP32 physically moves
the mask servos, instead of waiting for the servo movement to
finish first. This is what keeps the mask animation and JARVIS's
voice in sync instead of the voice lagging behind.

(Why this was needed: the ESP32's openMask()/closeMask() handlers
call synchronizeAllServosStartAndWaitForAllServosToStop(), which
blocks the ESP32 until the servos finish moving BEFORE it sends
back an HTTP response. The old blocking version of this function
waited on that response before even starting TTS synthesis, so the
mask always finished moving well before JARVIS started speaking.)

Requires: pip install requests
"""

import threading

import requests

from commands.helmet_commands import COMMAND_RESPONSES, NONE
from config import ESP32_IP, ESP32_HTTP_PORT, ESP32_REQUEST_TIMEOUT

ENDPOINT_MAP = {
    "OPEN_HELMET": "open",
    "CLOSE_HELMET": "close",
    "LIGHTS_ON": "lights_on",
    "LIGHTS_OFF": "lights_off",
    "COMBAT_MODE": "combat_mode",
    "PARTY_MODE": "party_mode",
    "NORMAL_MODE": "normal_mode",
}


def _send_http_command(endpoint: str) -> None:
    """
    Sends a GET request to the ESP32's HTTP endpoint. Runs in a
    background thread -- failures are logged but never crash the
    assistant, and nothing waits on this to finish.
    """
    url = f"http://{ESP32_IP}:{ESP32_HTTP_PORT}/{endpoint}"
    try:
        response = requests.get(url, timeout=ESP32_REQUEST_TIMEOUT)
        if response.status_code == 200:
            print(f"[ESP32] Sent: {endpoint} -> {response.text}")
        else:
            print(f"[ESP32] Unexpected response ({response.status_code}) for {endpoint}")
    except requests.exceptions.RequestException as e:
        print(f"[ESP32] Could not reach {url}: {e}")


def execute_command(command: str) -> str:
    """
    Fires off a helmet command to the ESP32 over WiFi in the
    background and returns a human-readable confirmation string
    immediately -- it does NOT wait for the ESP32 to finish moving
    the servos, so the caller (main.py) can start generating and
    playing the spoken reply right away, in parallel with the
    physical mask movement.
    """
    if command == NONE:
        return ""

    message = COMMAND_RESPONSES.get(command, f"Executing {command}.")
    endpoint = ENDPOINT_MAP.get(command)

    if endpoint is not None:
        threading.Thread(target=_send_http_command, args=(endpoint,), daemon=True).start()
    else:
        print(f"[ESP32] No WiFi endpoint mapped for command: {command}")

    return message
