import glob
import os
import shutil
import subprocess

import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SARVAM_PIECE_SECONDS = 25

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

# Initialize Groq client once.
groq_client = Groq(api_key=GROQ_API_KEY)


def _ffmpeg_binary() -> str:
    env_location = os.getenv("FFMPEG_LOCATION", "").strip()
    if env_location:
        if os.path.isdir(env_location):
            candidate = os.path.join(env_location, "ffmpeg.exe")
            if os.path.exists(candidate):
                return candidate
        elif os.path.exists(env_location):
            return env_location

    resolved = shutil.which("ffmpeg")
    if resolved:
        return resolved

    try:
        import imageio_ffmpeg  # type: ignore

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.exists(bundled):
            return bundled
    except Exception:
        pass

    raise RuntimeError(
        "FFmpeg executable not found. Install FFmpeg and add it to PATH, "
        "or set FFMPEG_LOCATION to ffmpeg.exe (or its folder), or install "
        "'imageio-ffmpeg' in the current environment."
    )


def _run_ffmpeg(command: list[str]) -> None:
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "FFmpeg is not installed or not available on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or "Unknown FFmpeg error"
        raise RuntimeError(f"FFmpeg failed: {details}") from exc


def _split_for_sarvam(chunk_path: str) -> list[str]:
    piece_pattern = f"{chunk_path}_sv_%03d.wav"
    ffmpeg = _ffmpeg_binary()

    for existing in glob.glob(f"{chunk_path}_sv_*.wav"):
        os.remove(existing)

    _run_ffmpeg(
        [
            ffmpeg,
            "-y",
            "-i",
            chunk_path,
            "-f",
            "segment",
            "-segment_time",
            str(SARVAM_PIECE_SECONDS),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            piece_pattern,
        ]
    )

    pieces = sorted(glob.glob(f"{chunk_path}_sv_*.wav"))
    if not pieces:
        raise RuntimeError("Failed to split audio for Sarvam transcription.")

    return pieces


def transcribe_chunk_groq(chunk_path: str) -> str:
    """
    Transcribe audio using Groq Whisper API.
    """

    with open(chunk_path, "rb") as audio_file:
        transcription = groq_client.audio.transcriptions.create(
            file=(os.path.basename(chunk_path), audio_file.read()),
            model="whisper-large-v3",
            response_format="text",
            language="en",
        )

    return transcription.strip()


def _send_to_sarvam(piece_path: str) -> str:
    """
    Send one <=30s WAV file to Sarvam and return transcript.
    """

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    with open(piece_path, "rb") as f:
        files = {
            "file": (os.path.basename(piece_path), f, "audio/wav")
        }

        data = {
            "model": SARVAM_MODEL,
            "with_diarization": "false"
        }

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\nSarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts <=30s audio.
    Split into 25-second pieces.
    """

    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    full_text = ""
    pieces = _split_for_sarvam(chunk_path)
    total_pieces = len(pieces)

    for i, piece_path in enumerate(pieces):
        try:
            print(f"  -> Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(
    chunk_path: str,
    language: str = "english"
) -> str:
    """
    Route chunk to:
    - english  -> Groq Whisper
    - hinglish -> Sarvam
    """

    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)

    return transcribe_chunk_groq(chunk_path)


def transcribe_all(
    chunks: list,
    language: str = "english"
) -> str:

    full_transcript = ""

    engine = (
        "Sarvam AI"
        if language.lower() == "hinglish"
        else "Groq Whisper"
    )

    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        text = transcribe_chunk(
            chunk,
            language=language
        )

        full_transcript += text + " "

    print("Transcription complete.")

    return full_transcript.strip()
