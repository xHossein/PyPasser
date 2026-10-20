"""Audio challenge helpers for reCaptcha V2.

The challenge mp3 is downloaded here and handed to :mod:`pypasser.speech` for
decoding and transcription.

Requires the ``speech`` extra::

    pip install PyPasser[speech]
"""

from __future__ import annotations

import os

from pypasser.speech import convert_to_wav, load_model, transcribe_file

DEFAULT_MODEL = "vosk-model-small-en-us-0.15"


def speech_to_text(wav_path: str, model_name: str = DEFAULT_MODEL) -> str:
    """Transcribe a 16 kHz mono wav file with vosk (offline engine)."""
    return transcribe_file(wav_path, load_model(name=model_name))


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


__all__ = ["DEFAULT_MODEL", "convert_to_wav", "download_audio", "speech_to_text"]
