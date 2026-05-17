<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MeetMind AI</title>
</head>

<body>

  <h1>MeetMind AI</h1>

  <p>
    MeetMind AI is an intelligent multilingual meeting assistant that transforms
    meeting audio and video into structured, searchable knowledge using modern
    LLM and Retrieval-Augmented Generation (RAG) pipelines.
  </p>

  <p>
    The system supports transcription, summarization, action item extraction,
    key decision tracking, open question identification, and contextual chat
    over meeting transcripts.
  </p>

  <hr />

  <h2>Live Demo</h2>

  <p>
    <a href="https://meetmind-ai-hmg7njl33spfqt2snguyyf.streamlit.app/" target="_blank">
      Launch MeetMind AI
    </a>
  </p>

  <hr />

  <h2>Core Features</h2>

  <ul>
    <li>Multilingual AI transcription</li>
    <li>Meeting summarization</li>
    <li>Action item extraction</li>
    <li>Key decision tracking</li>
    <li>Open question identification</li>
    <li>RAG-powered conversational chat</li>
    <li>YouTube and file upload support</li>
    <li>Server-side quota enforcement</li>
  </ul>

  <hr />

  <h2>Technology Stack</h2>

  <ul>
    <li>Streamlit</li>
    <li>ChromaDB</li>
    <li>SQLite</li>
    <li>LangChain</li>
    <li>Groq Whisper</li>
    <li>Sarvam STT</li>
    <li>Mistral AI</li>
    <li>FFmpeg</li>
    <li>yt-dlp</li>
  </ul>

  <hr />

  <h2>Architecture Overview</h2>

  <pre>
Audio / Video Input
        ↓
Speech-to-Text Pipeline
(Groq Whisper / Sarvam STT)
        ↓
Transcript Processing
        ↓
LLM Extraction Pipeline
 ├── Summary
 ├── Action Items
 ├── Key Decisions
 └── Open Questions
        ↓
Embedding Generation
        ↓
ChromaDB Vector Store
        ↓
RAG Conversational Retrieval
  </pre>

  <hr />

  <h2>Project Structure</h2>

  <pre>
project/
├── app.py
├── main.py
├── usage.py
├── core/
│   ├── transcriber.py
│   ├── summarize.py
│   ├── extractor.py
│   ├── rag_engine.py
│   └── vector_store.py
├── utils/
│   ├── audio_processor.py
│   └── runtime_setup.py
├── downloads/
├── vector_db/
├── requirements.txt
└── .gitignore
  </pre>

  <hr />

  <h2>Installation</h2>

  <pre>
pip install -r requirements.txt
  </pre>

  <hr />

  <h2>Run Application</h2>

  <h3>Streamlit App</h3>

  <pre>
streamlit run app.py
  </pre>

  <h3>CLI Mode</h3>

  <pre>
python main.py
  </pre>

  <hr />

  <h2>Environment Variables</h2>

  <pre>
GROQ_API_KEY=your_groq_api_key
MISTRAL_API_KEY=your_mistral_api_key
SARVAM_API_KEY=your_sarvam_api_key

SARVAM_STT_MODEL=saaras:v2.5
FFMPEG_LOCATION=
  </pre>

  <hr />

  <h2>Usage Limits</h2>

  <p>
    MeetMind AI enforces secure server-side monthly quotas using SQLite.
  </p>

  <ul>
    <li>4 successful requests per user per month</li>
    <li>Failure-safe transaction workflow</li>
    <li>Failed requests do not consume quota</li>
  </ul>

  <hr />

  <h2>Deployment Notes</h2>

  <p>
    The application is optimized for Streamlit Community Cloud deployment.
  </p>

  <p>
    YouTube downloads may occasionally fail on shared cloud infrastructure
    because of provider anti-bot restrictions. File uploads are the recommended
    primary workflow for stable processing.
  </p>

  <hr />

  <h2>Use Cases</h2>

  <ul>
    <li>Team meeting intelligence</li>
    <li>Interview summarization</li>
    <li>Lecture transcription</li>
    <li>Webinar analysis</li>
    <li>Knowledge retrieval systems</li>
  </ul>

  <hr />

  <h2>License</h2>

  <p>
    This project is intended for educational, research, and portfolio purposes.
  </p>

</body>
</html>