"""Answer strategy for the GeeTest V4 ``voice``."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional, Sequence, Tuple

from pypasser.exceptions import GeeTestSolveFailed

SAMPLE_RATE = 16000
_MODELS: Dict[Optional[str], Any] = {}

DEFAULT_LANG = "en-us"

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
        Directory of a Vosk model. When omitted the English model named by
        :data:`DEFAULT_LANG` is used; Vosk downloads it on first use.
    """
    return digits(_recognize(_to_pcm(audio), model_path))


def _to_pcm(audio: bytes) -> bytes:
    """Decode any container to 16 kHz mono signed-16 PCM via ffmpeg."""
    try:
        import imageio_ffmpeg
    except ImportError as exc:  # pragma: no cover - dependency error path
        raise GeeTestSolveFailed(
            "voice challenges need the 'speech' extra: pip install PyPasser[speech]"
        ) from exc
    try:
        completed = subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-v",
                "quiet",
                "-i",
                "pipe:0",
                "-ar",
                str(SAMPLE_RATE),
                "-ac",
                "1",
                "-f",
                "s16le",
                "-",
            ],
            input=audio,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise GeeTestSolveFailed(f"ffmpeg could not decode the audio: {exc}") from exc
    return completed.stdout


def _recognize(pcm: bytes, model_path: Optional[str]) -> str:
    try:
        import vosk
    except ImportError as exc:  # pragma: no cover - dependency error path
        raise GeeTestSolveFailed(
            "voice challenges need the 'speech' extra: pip install PyPasser[speech]"
        ) from exc

    vosk.SetLogLevel(-1)
    model = _model(vosk, model_path)
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE, json.dumps(list(_GRAMMAR)))
    recognizer.AcceptWaveform(pcm)
    return json.loads(recognizer.FinalResult()).get("text", "")


def _model(vosk: Any, model_path: Optional[str]) -> Any:
    """The Vosk model for ``model_path``, loaded once per process.

    Loading costs about a second and the model is immutable, so repeats of the
    same solve reuse it.
    """
    if model_path not in _MODELS:
        _MODELS[model_path] = (
            vosk.Model(model_path) if model_path else vosk.Model(lang=DEFAULT_LANG)
        )
    return _MODELS[model_path]


def answer_fields(audio: bytes, model_path: Optional[str] = None) -> dict:
    """The risk_type-specific part of the verify payload."""
    text = transcribe(audio, model_path)
    if not text:
        raise GeeTestSolveFailed("voice audio decoded to no digits")
    return {"userresponse": text}


__all__: Sequence[str] = ["answer_fields", "digits", "transcribe"]
