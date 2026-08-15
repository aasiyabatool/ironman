"""
commands/status_led.py
--------------------------
Sends the assistant's current pipeline state to the ESP32 so the
eye LEDs reflect it visually:

    Blue   = Listening (wake word heard, recording your command)
    Green  = Ready (idle, waiting for the wake word)
    Yellow = Processing (transcribing / thinking / generating speech)
    Red    = Error (something went wrong)

This is deliberately best-effort: a failed status update should
never interrupt or crash the actual voice pipeline, so all errors
are caught and logged, not raised.
"""

import requests

from config import ESP32_IP, ESP32_HTTP_PORT

STATUS_ENDPOINTS = {
    "listening": "status_listening",
    "ready": "status_ready",
    "processing": "status_processing",
    "error": "status_error",
}

# Status updates should be fast and non-critical -- a short timeout
# means a slow/unreachable ESP32 never noticeably delays JARVIS.
STATUS_REQUEST_TIMEOUT = 1.5

# Values that mean "no helmet configured" -- covers an unset/blank
# ESP32_IP (config.py already normalizes that to None), plus common
# placeholder strings someone might leave in .env while testing
# without the helmet powered on.
_MISSING_IP_VALUES = {"none", "null", "false", "0.0.0.0", ""}


def _has_valid_esp32_ip() -> bool:
    if ESP32_IP is None:
        return False
    return ESP32_IP.strip().lower() not in _MISSING_IP_VALUES


def set_status(state: str) -> None:
    """
    Updates the ESP32's status LEDs.

    Args:
        state: one of "listening", "ready", "processing", "error".
    """
    endpoint = STATUS_ENDPOINTS.get(state)
    if endpoint is None:
        print(f"[StatusLED] Unknown status: {state}")
        return

    if not _has_valid_esp32_ip():
        # No helmet configured/plugged in -- skip the request entirely
        # instead of letting requests hit DNS resolution or connect
        # against a missing/placeholder host and raise
        # ConnectTimeoutError/NameResolutionError.
        return

    url = f"http://{ESP32_IP}:{ESP32_HTTP_PORT}/{endpoint}"
    try:
        requests.get(url, timeout=STATUS_REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        # Don't let a status LED failure interrupt the actual
        # assistant -- just log it and move on.
        print(f"[StatusLED] Could not update status to '{state}': {e}")
