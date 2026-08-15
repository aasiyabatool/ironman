"""
commands/helmet_commands.py
-----------------------------
Defines the set of valid helmet commands and the spoken
phrases that map to each one.
"""

OPEN_HELMET = "OPEN_HELMET"
CLOSE_HELMET = "CLOSE_HELMET"
LIGHTS_ON = "LIGHTS_ON"
LIGHTS_OFF = "LIGHTS_OFF"
COMBAT_MODE = "COMBAT_MODE"
PARTY_MODE = "PARTY_MODE"
NORMAL_MODE = "NORMAL_MODE"
NONE = "NONE"

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
    COMBAT_MODE: [
        "combat mode",
        "activate combat mode",
        "engage combat mode",
    ],
    PARTY_MODE: [
        "party mode",
        "activate party mode",
        "start party mode",
    ],
    NORMAL_MODE: [
        "normal mode",
        "stop party mode",
        "stop combat mode",
        "cancel mode",
        "exit party mode",
        "exit combat mode",
    ],
}

COMMAND_RESPONSES = {
    OPEN_HELMET: "Opening helmet.",
    CLOSE_HELMET: "Closing helmet.",
    LIGHTS_ON: "Lights on.",
    LIGHTS_OFF: "Lights off.",
    COMBAT_MODE: "Combat mode engaged.",
    PARTY_MODE: "Let's party.",
    NORMAL_MODE: "Returning to normal mode.",
}
