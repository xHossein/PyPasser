"""Speech-to-text primitives shared by the voice-based solvers.

Requires the ``speech`` extra::

    pip install PyPasser[speech]
"""

from __future__ import annotations

from pypasser.speech.asr import load_model, recognize_pcm, transcribe_file
from pypasser.speech.ffmpeg import (
    SAMPLE_RATE,
    cleanup_audio,
    convert_to_wav,
    decode_to_pcm,
    ensure_ffmpeg,
)

__all__ = [
    "SAMPLE_RATE",
    "cleanup_audio",
    "convert_to_wav",
    "decode_to_pcm",
    "ensure_ffmpeg",
    "load_model",
    "recognize_pcm",
    "transcribe_file",
]
