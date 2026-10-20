"""Persian voice-challenge transcription.

ARCaptcha voice challenges are short (~1 s) Persian word clips served as mp3.
The answer is the spoken word, so the challenge is a small ASR task.

The small Persian model is not accurate enough on these clips; the big model
(``vosk-model-fa-0.42``, ~1.6 GB) transcribes them correctly and is downloaded
on first use. Decoding and the model cache live in :mod:`pypasser.speech`.
"""

from __future__ import annotations

import re

from pypasser.speech import convert_to_wav, load_model, transcribe_file

DEFAULT_MODEL = "vosk-model-fa-0.42"


def normalize_text(text: str) -> str:
    """Normalize a Persian transcript for answer matching.

    The server compares against its own normalized forms: zero-width
    non-joiners and tatweel (kashida) are dropped, the Arabic yeh/kaf are
    mapped to their Persian counterparts, and whitespace is collapsed.
    """
    text = text.replace("‌", "").replace("ـ", "")
    text = text.replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", text).strip()


def transcribe(mp3_path: str, model_name: str | None = None) -> str:
    """Transcribe a voice challenge mp3 and return the normalized answer text.

    Parameters
    ----------
    mp3_path: str
        The downloaded challenge mp3.
    model_name: str, optional
        vosk model name; defaults to the big Persian model (downloaded on
        first use, ~1.6 GB — the small one is not accurate enough).
    """
    model = load_model(name=model_name or DEFAULT_MODEL)
    wav_path = convert_to_wav(mp3_path)
    return normalize_text(transcribe_file(wav_path, model))


__all__ = ["DEFAULT_MODEL", "normalize_text", "transcribe"]
