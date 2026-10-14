"""Persian voice-challenge transcription (vosk + ffmpeg).

ARCaptcha voice challenges are short (~1 s) Persian word clips served as
mp3. The answer is the spoken word, so the challenge is a small ASR task.

The small Persian model is not accurate enough on these clips; the big
model (``vosk-model-fa-0.42``, ~1.6 GB) transcribes them correctly. It is
downloaded on first use, exactly like the English model in the reCaptcha V2
audio helper.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import wave

DEFAULT_MODEL = "vosk-model-fa-0.42"

_MODEL_CACHE: dict[str, object] = {}
_FFMPEG_CONFIGURED = False


def _ensure_ffmpeg() -> str:
    """Return an ffmpeg executable path, configuring pydub if needed."""
    global _FFMPEG_CONFIGURED

    system = shutil.which("ffmpeg")
    if system:
        return system

    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        binary = get_ffmpeg_exe()
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "ffmpeg not found. Install it from https://ffmpeg.org or "
            "via pip: pip install imageio-ffmpeg (included in PyPasser[speech])."
        ) from exc

    if not _FFMPEG_CONFIGURED:
        from pydub import AudioSegment

        AudioSegment.converter = binary
        _FFMPEG_CONFIGURED = True

    return binary


def convert_to_wav(mp3_path: str) -> str:
    """Convert an mp3 file to 16 kHz mono wav (same path, new extension)."""
    try:
        from pydub import AudioSegment
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "pydub is required for audio conversion. Install it with: "
            "pip install PyPasser[speech]"
        ) from exc

    _ensure_ffmpeg()
    wav_path = os.path.splitext(mp3_path)[0] + ".wav"
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")
    return wav_path


def normalize_text(text: str) -> str:
    """Normalize a Persian transcript for answer matching.

    The server compares against its own normalized forms: zero-width
    non-joiners and tatweel (kashida) are dropped, the Arabic yeh/kaf are
    mapped to their Persian counterparts, and whitespace is collapsed.
    """
    text = text.replace("\u200c", "").replace("\u0640", "")
    text = text.replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")
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
    try:
        import vosk
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "vosk is required for the voice challenge. Install it with: "
            "pip install PyPasser[speech]"
        ) from exc

    name = model_name or DEFAULT_MODEL
    if name not in _MODEL_CACHE:
        vosk.SetLogLevel(-1)
        _MODEL_CACHE[name] = vosk.Model(model_name=name)

    wav_path = convert_to_wav(mp3_path)
    recognizer = vosk.KaldiRecognizer(_MODEL_CACHE[name], 16000)

    with wave.open(wav_path, "rb") as wf:
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            recognizer.AcceptWaveform(data)

    return normalize_text(json.loads(recognizer.FinalResult())["text"])
