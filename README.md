# AI Meeting Assistant

A Streamlit app that turns meeting audio/video into:
- transcript
- title + summary
- action items
- key decisions
- open questions
- chat over the meeting transcript (RAG)

## Stack

- Streamlit
- ChromaDB (local vector store)
- SQLite (hard monthly usage limits)
- Groq Whisper (English transcription)
- Sarvam STT (Hinglish transcription)
- Mistral (summary/extraction/RAG answers via LangChain)

## Features

- Input (recommended): file upload (audio/video)
- Optional fallback: YouTube URL or local file path
- Auto conversion/chunking with FFmpeg
- Two language modes:
  - `english` -> Groq Whisper
  - `hinglish` -> Sarvam STT
- RAG chat grounded in transcript context
- Hard quota enforcement:
  - 4 successful requests per user per month
  - enforced server-side in SQLite
  - failure-safe (failed requests do not consume quota)

## Project Structure

```text
project/
├── app.py                 # Streamlit UI + orchestration
├── main.py                # CLI pipeline entry
├── usage.py               # Hard monthly quota logic (SQLite)
├── core/
│   ├── transcriber.py     # Groq/Sarvam transcription routing
│   ├── summarize.py       # Meeting title + summary
│   ├── extractor.py       # Actions/decisions/questions extraction
│   ├── rag_engine.py      # RAG chain + query
│   └── vector_store.py    # Chroma vector store build/load
├── utils/
│   ├── audio_processor.py # download/convert/chunk
│   └── runtime_setup.py
├── downloads/             # temporary media/audio files
├── vector_db/             # Chroma persistence directory
├── requirements.txt
└── .gitignore
```

## Prerequisites

- Python 3.10+
- FFmpeg available via one of:
  - system PATH
  - `FFMPEG_LOCATION` env var
  - `imageio-ffmpeg` fallback (already in requirements)

## Environment Variables

Create a `.env` file in project root:

```env
GROQ_API_KEY=your_groq_api_key
MISTRAL_API_KEY=your_mistral_api_key
SARVAM_API_KEY=your_sarvam_api_key

# Optional
SARVAM_STT_MODEL=saaras:v2.5
FFMPEG_LOCATION=
```

## Installation

```bash
pip install -r requirements.txt
```

## Run

Streamlit app:

```bash
streamlit run app.py
```

CLI mode:

```bash
python main.py
```

## Hard Rate Limits (Mandatory)

Quota is implemented in `usage.py` using SQLite transactions.

- Monthly limit: `4`
- Scope: per resolved `user_id`
- Workflow:
  - `reserve_quota(user_id)` before expensive processing
  - `commit_quota(user_id)` only after successful response
  - `release_quota(user_id)` on exception

This prevents race conditions and avoids charging failed requests.

If no authenticated identity is present in `st.session_state`, the app falls back to a generated guest session id.

## Deployment Notes

### Streamlit Community Cloud

Works well for demos, but local filesystem persistence is not guaranteed across restarts/redeploys.

That means these may reset:
- `usage.db`
- `vector_db/`
- `downloads/`

For stronger persistence in production, move usage/vector metadata to managed services (for example Postgres/Supabase + hosted vector DB).

YouTube downloads may also fail intermittently on shared cloud IPs due to provider anti-bot/network policies. The app is designed so upload-based processing is the reliable primary path.

The YouTube downloader is configured with:
- modern `yt-dlp`
- browser-like headers
- `extractor_args` using YouTube `player_client=android`
- optional cookiefile support via `YTDLP_COOKIEFILE` (not recommended for public deployments)

### Secrets

Do not commit:
- `.env`
- `.streamlit/secrets.toml`
- `usage.db`

Already covered in `.gitignore`.

## Troubleshooting

- `FFmpeg executable not found`
  - Install FFmpeg or set `FFMPEG_LOCATION`.
- `ModuleNotFoundError` during deploy
  - Ensure dependency is listed in `requirements.txt`.
- Limit reached unexpectedly
  - Check current month rows in `usage.db` table `usage`.
