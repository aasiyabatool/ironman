"""
commands/helmet_commands.py
-----------------------------
Defines the set of valid helmet commands and the spoken
phrases that map to each one. Keeping this separate from
parser.py makes it trivial to add new commands later
(e.g. "raise visor", "scan area") without touching the
detection logic itself.
"""

OPEN_HELMET = "OPEN_HELMET"
CLOSE_HELMET = "CLOSE_HELMET"
LIGHTS_ON = "LIGHTS_ON"
LIGHTS_OFF = "LIGHTS_OFF"
NONE = "NONE"

# Each command maps to a list of trigger phrases (all lowercase).
# The parser checks if any of these phrases appear in the user's text.
COMMAND_PHRASES = {
    OPEN_HELMET: [
        "open helmet",
        "open the helmet",
        "helmet open",
        "open face plate",
        "open faceplate",
        "open mask",
        "open the mask",
        "raise visor",
        "raise the visor",
    ],
    CLOSE_HELMET: [
        "close helmet",
        "close the helmet",
        "helmet close",
        "close face plate",
        "close faceplate",
        "close mask",
        "close the mask",
        "seal helmet",
        "lower visor",
        "lower the visor",
    ],
    LIGHTS_ON: [
        "lights on",
        "turn on the lights",
        "turn the lights on",
        "eyes on",
    ],
    LIGHTS_OFF: [
        "lights off",
        "turn off the lights",
        "turn the lights off",
        "eyes off",
    ],
}

# Friendly confirmation messages returned by the simulator/ESP32
# after a command executes successfully.
COMMAND_RESPONSES = {
    OPEN_HELMET: "Opening helmet.",
    CLOSE_HELMET: "Closing helmet.",
    LIGHTS_ON: "Lights on.",
    LIGHTS_OFF: "Lights off.",
}
