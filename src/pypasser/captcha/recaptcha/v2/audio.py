"""Audio challenge helpers for reCaptcha V2.

The mp3 download is converted to 16 kHz mono wav and transcribed with vosk.

Requires the ``speech`` extra::

    pip install PyPasser[speech]
"""

from __future__ import annotations

import os
import shutil
import wave

DEFAULT_MODEL = "vosk-model-small-en-us-0.15"

_FFMPEG_CONFIGURED = False
_MODEL_CACHE: dict[str, object] = {}


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
    try:
        audio = AudioSegment.from_mp3(mp3_path)
    except Exception as exc:
        from pypasser.exceptions import IpBlock
        raise IpBlock(f"Failed to decode audio challenge: {exc}") from exc
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")
    return wav_path


def _load_model(model_name: str = DEFAULT_MODEL):
    """Load (and cache) a vosk model; downloads it on first use (~40 MB)."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    try:
        import vosk
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "vosk is required for the audio challenge. Install it with: "
            "pip install PyPasser[speech]"
        ) from exc

    vosk.SetLogLevel(-1)
    model = vosk.Model(model_name=model_name)
    _MODEL_CACHE[model_name] = model
    return model


def speech_to_text(wav_path: str, model_name: str = DEFAULT_MODEL) -> str:
    """Transcribe a 16 kHz mono wav file with vosk (offline engine)."""
    import json

    import vosk

    model = _load_model(model_name)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with wave.open(wav_path, "rb") as wf:
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            recognizer.AcceptWaveform(data)

    return json.loads(recognizer.FinalResult())["text"]


def _is_valid_mp3(data: bytes) -> bool:
    """Basic check for valid MP3 payload (ID3 header or MPEG sync word)."""
    if len(data) < 256:
        return False
    if data[:3] == b"ID3":
        return True
    # MPEG frame sync: 11 bits set (0xFF followed by 0xE0-0xFF)
    for i in range(min(len(data) - 1, 1024)):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            return True
    return False


def download_audio(link: str, dest_dir: str) -> str:
    """Download the challenge audio into ``dest_dir`` and return the file path."""
    import time
    from random import randint

    import httpx

    from pypasser.exceptions import IpBlock

    filename = f"{int(time.time())}_{randint(10000, 99999)}.mp3"
    dest_path = os.path.join(dest_dir, filename)

    response = httpx.get(link, timeout=30, follow_redirects=True)
    response.raise_for_status()

    content = response.content
    head = content[:500].lower()
    if b"<html" in head or b"<!doctype" in head or b"automated queries" in head:
        raise IpBlock("Google audio download returned an HTML block page.")

    if not _is_valid_mp3(content):
        raise IpBlock("Google audio download is not a valid MP3 (IP or session blocked).")

    with open(dest_path, "wb") as f:
        f.write(content)

    return dest_path
