import glob
import os
import re
import shutil
import subprocess
from uuid import uuid4

import yt_dlp
from yt_dlp.utils import DownloadError

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR,exist_ok=True)


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


def download_yt_audio(url:str)->str:
    output_path = os.path.join(DOWNLOAD_DIR,"%(title)s.%(ext)s")
    ffmpeg_path = _ffmpeg_binary()
    cookiefile = os.getenv("YTDLP_COOKIEFILE", "").strip()

    ytk_opts = {
        "format" : "bestaudio/best",
        "outtmpl" : output_path,
        "quiet" : True,
        "noplaylist": True,
        "ffmpeg_location": os.path.dirname(ffmpeg_path),
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        },
    }

    if cookiefile and os.path.exists(cookiefile):
        ytk_opts["cookiefile"] = cookiefile

    try:
        with yt_dlp.YoutubeDL(ytk_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except DownloadError as exc:
        raise RuntimeError(
            "YouTube download failed. This often happens on cloud deployments where "
            "shared datacenter IPs are blocked by YouTube. Please upload an audio/video "
            "file directly or try another video."
        ) from exc

    if os.path.exists(filename):
        return filename

    # Fallback for edge cases where yt-dlp sanitizes names unexpectedly.
    candidates = sorted(
        glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("YouTube audio download completed, but no media file was found.")

    filename = candidates[0]
    return filename


def convert_to_wav(input_path:str)->str:
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    ffmpeg = _ffmpeg_binary()

    _run_ffmpeg(
        [
            ffmpeg,
            "-y",
            "-i",
            input_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            output_path,
        ]
    )

    return output_path

def chunk_audio(wav_path : str,chunk_min : int =10) -> list:
    ffmpeg = _ffmpeg_binary()
    chunk_ms = chunk_min * 60 * 1000
    chunk_seconds = max(chunk_ms // 1000, 1)
    chunk_pattern = f"{wav_path}_chunk_%03d.wav"

    for existing in glob.glob(f"{wav_path}_chunk_*.wav"):
        os.remove(existing)

    _run_ffmpeg(
        [
            ffmpeg,
            "-y",
            "-i",
            wav_path,
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            chunk_pattern,
        ]
    )

    chunks = sorted(glob.glob(f"{wav_path}_chunk_*.wav"))
    if not chunks:
        raise RuntimeError("Audio chunking failed: no chunk files generated.")

    return chunks

def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "uploaded_media"


def save_uploaded_media(file_name: str, file_bytes: bytes) -> str:
    safe_name = _sanitize_filename(file_name)
    unique_name = f"{uuid4().hex[:10]}_{safe_name}"
    output_path = os.path.join(DOWNLOAD_DIR, unique_name)

    with open(output_path, "wb") as f:
        f.write(file_bytes)

    return output_path


def process_input(
    source: str = "",
    uploaded_file_name: str | None = None,
    uploaded_file_bytes: bytes | None = None,
) -> list:
    source = (source or "").strip()

    if uploaded_file_name and uploaded_file_bytes:
        print("Detected uploaded file. Saving and converting to WAV...")
        uploaded_path = save_uploaded_media(uploaded_file_name, uploaded_file_bytes)
        wav_path = convert_to_wav(uploaded_path)
    elif source.startswith("http://") or source.startswith("https://"):
        print("Detected Youtube URL. Downloading URL...")
        downloaded_path = download_yt_audio(source)
        print("Converting downloaded audio to WAV...")
        wav_path = convert_to_wav(downloaded_path)
    elif source:
        print("Deteted Local File. Converting to WAV...")
        wav_path = convert_to_wav(source)
    else:
        raise RuntimeError("No valid input provided. Upload a file or provide a URL/path.")

    print("Chunking Audio...")

    chunks = chunk_audio(wav_path)
    print(f"Audio Ready - {len(chunks)} chunk(s) created")
    return chunks

