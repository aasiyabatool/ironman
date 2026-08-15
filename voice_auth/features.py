"""
voice_auth/features.py
--------------------------
Extracts a fixed-length feature vector from an audio clip using
MFCCs (Mel-Frequency Cepstral Coefficients) -- a classic, effective
numerical representation of "voice timbre" that was the standard
approach for speaker recognition before deep learning became
dominant. It captures the shape of the vocal tract, which differs
meaningfully between speakers regardless of what words they're
saying.
"""

import numpy as np
import librosa

from voice_auth.config import SAMPLE_RATE, N_MFCC


def extract_features(audio_path: str) -> np.ndarray:
    """
    Loads an audio file and returns a fixed-length feature vector
    summarizing its MFCCs.

    A raw MFCC output has one value per coefficient PER TIME FRAME,
    so its size depends on how long the clip is -- not usable
    directly as input to a classifier that expects a fixed-size
    vector. Taking the mean and standard deviation of each
    coefficient across the whole clip collapses this into a fixed
    26-value vector (13 means + 13 std deviations) regardless of
    the recording's length.
    """
    audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)

    mfccs = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=N_MFCC)

    mfcc_mean = np.mean(mfccs, axis=1)
    mfcc_std = np.std(mfccs, axis=1)

    return np.concatenate([mfcc_mean, mfcc_std])
