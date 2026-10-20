"""ffmpeg discovery and audio decoding shared by every voice challenge."""

from __future__ import annotations

import os
import shutil
import subprocess

from pypasser.exceptions import AudioDecodeError

SAMPLE_RATE = 16000

_pydub_configured = False


def ensure_ffmpeg() -> str:
    """Return an ffmpeg executable path, configuring pydub on the imageio fallback."""
    global _pydub_configured

    system = shutil.which("ffmpeg")
    if system:
        return system

    try:
        from imageio_ffmpeg import get_ffmpeg_exe
    except ImportError as exc:
        raise ImportError(
            "ffmpeg not found. Install it from https://ffmpeg.org or "
            "via pip: pip install imageio-ffmpeg (included in PyPasser[speech])."
        ) from exc

    binary = get_ffmpeg_exe()
    if not _pydub_configured:
        from pydub import AudioSegment

        AudioSegment.converter = binary
        _pydub_configured = True
    return binary


def convert_to_wav(mp3_path: str, sample_rate: int = SAMPLE_RATE) -> str:
    """Convert an mp3 file to mono wav (same path, new extension)."""
    try:
        from pydub import AudioSegment
    except ImportError as exc:
        raise ImportError(
            "pydub is required for audio conversion. Install it with: "
            "pip install PyPasser[speech]"
        ) from exc

    ensure_ffmpeg()
    wav_path = os.path.splitext(mp3_path)[0] + ".wav"
    try:
        audio = AudioSegment.from_mp3(mp3_path)
    except Exception as exc:
        raise AudioDecodeError(f"failed to decode {mp3_path}: {exc}") from exc
    audio.set_channels(1).set_frame_rate(sample_rate).export(wav_path, format="wav")
    return wav_path


def cleanup_audio(mp3_path: str) -> None:
    """Remove a clip and the wav ``convert_to_wav`` derived from it."""
    for path in (mp3_path, os.path.splitext(mp3_path)[0] + ".wav"):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def decode_to_pcm(audio: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Decode any container ffmpeg can read to mono signed-16 PCM."""
    ffmpeg = ensure_ffmpeg()
    try:
        completed = subprocess.run(
            [
                ffmpeg,
                "-v",
                "quiet",
                "-i",
                "pipe:0",
                "-ar",
                str(sample_rate),
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
    except (subprocess.CalledProcessError, OSError) as exc:
        raise AudioDecodeError(f"ffmpeg could not decode the audio: {exc}") from exc
    return completed.stdout


__all__ = [
    "SAMPLE_RATE",
    "cleanup_audio",
    "convert_to_wav",
    "decode_to_pcm",
    "ensure_ffmpeg",
]
