import glob
import os
import shutil
import subprocess

import yt_dlp

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

    ytk_opts = {
        "format" : "bestaudio/best",
        "outtmpl" : output_path,
        "quiet" : True,
        "noplaylist": True,
        "ffmpeg_location": os.path.dirname(ffmpeg_path),
    }

    with yt_dlp.YoutubeDL(ytk_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if os.path.exists(filename):
        return filename

    # Fallback for edge cases where yt-dlp sanitizes names unexpectedly.
    candidates = sorted(
        glob.glob(os.path.join(DOWNLOAD_DIR, "*.wav")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError("YouTube audio download completed, but no WAV file was found.")

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

def process_input(source : str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected Youtube URL. Downloading URL...")
        downloaded_path = download_yt_audio(source)
        print("Converting downloaded audio to WAV...")
        wav_path = convert_to_wav(downloaded_path)

    else:
        print("Deteted Local File. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking Audio...")

    chunks = chunk_audio(wav_path)
    print(f"Audio Ready - {len(chunks)} chunk(s) created")
    return chunks

