"""Vosk model cache and offline recognition."""

from __future__ import annotations

import json
import threading
import wave
from typing import Any, Optional, Sequence

from pypasser.speech.ffmpeg import SAMPLE_RATE

_MODEL_CACHE: dict[tuple, Any] = {}
_MODEL_LOCK = threading.Lock()


def _vosk() -> Any:
    try:
        import vosk
    except ImportError as exc:
        raise ImportError(
            "vosk is required for voice challenges. Install it with: "
            "pip install PyPasser[speech]"
        ) from exc
    vosk.SetLogLevel(-1)
    return vosk


def load_model(
    *,
    name: Optional[str] = None,
    path: Optional[str] = None,
    lang: Optional[str] = None,
) -> Any:
    """Load a Vosk model once per process.

    Exactly one of ``path`` (a local model directory), ``name`` (a model
    directory name Vosk downloads on first use) or ``lang`` (a language code
    Vosk maps to its default model) is used, in that order.
    """
    key = (name, path, lang)
    model = _MODEL_CACHE.get(key)
    if model is not None:
        return model

    vosk = _vosk()
    with _MODEL_LOCK:
        model = _MODEL_CACHE.get(key)
        if model is None:
            if path:
                model = vosk.Model(path)
            elif name:
                model = vosk.Model(model_name=name)
            else:
                model = vosk.Model(lang=lang)
            _MODEL_CACHE[key] = model
    return model


def recognize_pcm(
    pcm: bytes,
    model: Any,
    grammar: Optional[Sequence[str]] = None,
    sample_rate: int = SAMPLE_RATE,
) -> str:
    """Transcribe raw 16-bit mono PCM, optionally restricted to ``grammar``."""
    vosk = _vosk()
    if grammar is None:
        recognizer = vosk.KaldiRecognizer(model, sample_rate)
    else:
        recognizer = vosk.KaldiRecognizer(model, sample_rate, json.dumps(list(grammar)))
    recognizer.AcceptWaveform(pcm)
    return json.loads(recognizer.FinalResult()).get("text", "")


def transcribe_file(path: str, model: Any, sample_rate: int = SAMPLE_RATE) -> str:
    """Transcribe a 16-bit mono wav file."""
    vosk = _vosk()
    recognizer = vosk.KaldiRecognizer(model, sample_rate)
    with wave.open(path, "rb") as wf:
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            recognizer.AcceptWaveform(data)
    return json.loads(recognizer.FinalResult())["text"]


__all__ = ["load_model", "recognize_pcm", "transcribe_file"]
