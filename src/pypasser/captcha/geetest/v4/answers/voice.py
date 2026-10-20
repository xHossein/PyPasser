"""Answer strategy for the GeeTest V4 ``voice`` risk type."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from pypasser.exceptions import AudioDecodeError, GeeTestSolveFailed
from pypasser.speech import SAMPLE_RATE, decode_to_pcm, load_model, recognize_pcm

# Vosk's language code for the English model, not the ``/load`` lang.
VOICE_MODEL_LANG = "en-us"

# The words the recognizer is allowed to emit. Anything else (the carrier
# phrase) collapses into [unk] and is dropped.
_GRAMMAR: Tuple[str, ...] = (
    "zero",
    "oh",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "[unk]",
)

_WORDS = {
    "zero": "0",
    "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}


def digits(transcript: str) -> str:
    """Map a transcript's number words to a digit string."""
    return "".join(_WORDS[word] for word in transcript.split() if word in _WORDS)


def transcribe(audio: bytes, model_path: Optional[str] = None) -> str:
    """Decode an audio clip to a digit string.

    Parameters
    ----------
    audio: bytes
        The challenge audio, in any container ffmpeg can read.
    model_path: str, optional
        Directory of a Vosk model. When omitted Vosk's English model is used
        and downloaded on first use.
    """
    try:
        pcm = decode_to_pcm(audio, sample_rate=SAMPLE_RATE)
        model = _model(model_path)
        return digits(recognize_pcm(pcm, model, _GRAMMAR, SAMPLE_RATE))
    except (ImportError, AudioDecodeError) as exc:
        raise GeeTestSolveFailed(f"voice challenge failed: {exc}") from exc


def _model(model_path: Optional[str]) -> Any:
    """The Vosk model for ``model_path``, loaded once per process."""
    if model_path:
        return load_model(path=model_path)
    return load_model(lang=VOICE_MODEL_LANG)


def answer_fields(audio: bytes, model_path: Optional[str] = None) -> dict:
    """The risk_type-specific part of the verify payload."""
    text = transcribe(audio, model_path)
    if not text:
        raise GeeTestSolveFailed("voice audio decoded to no digits")
    return {"userresponse": text}


__all__ = ["VOICE_MODEL_LANG", "answer_fields", "digits", "transcribe"]
