"""
voice_auth/config.py
------------------------
Settings for the speaker verification (voice authentication) system.

Supports MULTIPLE authorized people: each gets their own named
folder under voice_auth_data/, plus a special "unknown" folder for
non-authorized voices (so the model can also recognize "this is
nobody I know" rather than being forced to guess between only the
people you've enrolled).
"""

import os

VOICE_AUTH_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(VOICE_AUTH_DIR)

TRAINING_DATA_DIR = os.path.join(BASE_DIR, "voice_auth_data")

# Reserved folder name for non-authorized / background voice samples.
UNKNOWN_LABEL = "unknown"
UNKNOWN_DIR = os.path.join(TRAINING_DATA_DIR, UNKNOWN_LABEL)

MODEL_PATH = os.path.join(BASE_DIR, "models", "voice_auth_model.pkl")

SAMPLE_RATE = 16000
RECORD_SECONDS = 3   # length of each enrollment/test sample
N_MFCC = 13           # number of MFCC coefficients to extract

# Verification threshold: the model outputs a probability (0-1) for
# its best-matching identity. At or above this value, that identity
# is accepted. Raise this for stricter security (fewer false
# accepts, more false rejects); lower it if it's rejecting
# authorized people too often.
VOICE_AUTH_THRESHOLD = float(os.getenv("VOICE_AUTH_THRESHOLD", "0.75"))

# Master on/off switch for wiring this into the live pipeline later.
VOICE_AUTH_ENABLED = os.getenv("VOICE_AUTH_ENABLED", "false").lower() == "true"

os.makedirs(TRAINING_DATA_DIR, exist_ok=True)
os.makedirs(UNKNOWN_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
