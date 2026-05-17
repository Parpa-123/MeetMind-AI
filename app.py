import streamlit as st
from dotenv import load_dotenv
import html
import re
from uuid import uuid4

from utils.runtime_setup import configure_runtime
from utils.audio_processor import process_input

from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title

from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)

from core.rag_engine import (
    build_rag_chain,
    ask_question,
)
from usage import (
    MONTHLY_LIMIT,
    reserve_quota,
    commit_quota,
    release_quota,
    remaining_quota,
)

# ── Setup ──────────────────────────────────────────────────────────────────────
configure_runtime()
load_dotenv()

st.set_page_config(
    page_title="Meeting Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1117;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea {
    background: #1a1f2e !important;
    border: 1px solid #2d3448 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* Main */
.stApp { background: #0b0f1a; }
.main .block-container { padding: 2rem 2.5rem; max-width: 1200px; }

/* Cards */
.mi-card {
    background: #111827;
    border: 1px solid #1e2a3a;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.mi-card-title {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.75rem;
}

/* Metric grid */
.mi-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 1rem;
}
.mi-metric {
    background: #111827;
    border: 1px solid #1e2a3a;
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
}
.mi-metric-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 0.5rem;
}
.mi-metric-value {
    font-size: 1.9rem;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1;
}
.mi-metric-sub {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 4px;
}

/* List items */
.mi-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid #1a2235;
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.55;
}
.mi-item:last-child { border-bottom: none; }
.mi-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
}

/* Badges */
.mi-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: 0.68rem;
    font-weight: 600;
    flex-shrink: 0;
}
.badge-high   { background: #3b1a1a; color: #f87171; }
.badge-medium { background: #2d2310; color: #fbbf24; }
.badge-low    { background: #0f2918; color: #4ade80; }
.badge-confirmed { background: #0c2318; color: #34d399; }
.badge-pending   { background: #2d2310; color: #fbbf24; }

/* Transcript */
.mi-transcript {
    background: #0d1321;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: #8899aa;
    line-height: 1.85;
    max-height: 460px;
    overflow-y: auto;
    white-space: pre-wrap;
}
.mi-speaker {
    color: #6366f1;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 2px;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.mi-speaker:first-child { margin-top: 0; }

/* Chat */
.mi-chat-wrap {
    background: #111827;
    border: 1px solid #1e2a3a;
    border-radius: 14px;
    padding: 1rem 1.25rem;
    max-height: 480px;
    overflow-y: auto;
    margin-bottom: 1rem;
}
.mi-msg-user {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    font-size: 0.88rem;
    color: #c7d2fe;
}
.mi-msg-ai {
    background: #0d1321;
    border: 1px solid #1e2a3a;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.65;
}
.mi-sender {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 5px;
}

/* Page title */
.mi-page-title {
    font-size: 2rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 4px;
}
.mi-page-sub {
    font-size: 0.9rem;
    color: #475569;
    margin-bottom: 2rem;
}

/* Meeting title card */
.mi-meeting-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: #f1f5f9;
}

/* Section heading */
.mi-section-heading {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.75rem;
    margin-top: 0.25rem;
}

/* Empty state */
.mi-empty {
    border: 1px dashed #1e2a3a;
    border-radius: 18px;
    padding: 5rem 2rem;
    text-align: center;
    background: rgba(255,255,255,0.01);
}
.mi-empty-title {
    font-size: 1.4rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 0.75rem;
}
.mi-empty-sub {
    color: #475569;
    max-width: 460px;
    margin: auto;
    line-height: 1.8;
    font-size: 0.9rem;
}

/* Buttons */
.stButton > button {
    background: #6366f1 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    height: 42px !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Text input */
.stTextInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1e2a3a !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-size: 0.88rem !important;
}

/* Tab bar */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 4px;
    border-bottom: 1px solid #1e2a3a;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    color: #64748b !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #a5b4fc !important;
    border-bottom: 2px solid #6366f1 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.25rem !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #111827 !important;
    border: 1px solid #1e2a3a !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
    font-size: 0.88rem !important;
}

/* Alerts */
.stAlert { border-radius: 10px !important; }

/* Sidebar logo */
.mi-sidebar-logo {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.mi-sidebar-sub {
    font-size: 0.78rem;
    color: #475569;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


if "guest_user_id" not in st.session_state:
    st.session_state.guest_user_id = f"guest-{uuid4().hex[:12]}"


def resolve_user_id() -> str:
    """Resolve a stable user identifier for quota enforcement."""
    for key in ("email", "username", "user_email", "user_id", "name"):
        value = st.session_state.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return st.session_state.guest_user_id


def _normalize_chat_content(content: str) -> str:
    """Normalize LLM chat output so UI wrapper markup does not leak into messages."""
    text = str(content or "").strip()

    # Unwrap single fenced blocks that sometimes contain rendered HTML wrappers.
    fence_match = re.match(r"^```(?:html|markdown|text)?\s*([\s\S]*?)\s*```$", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # Remove accidental wrapper tags if the model echoes UI markup.
    text = re.sub(
        r'<div class="mi-sender">\s*(?:Assistant|You)\s*</div>',
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'</?div class="mi-msg-(?:ai|user)"\s*>',
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"</?div\s*>", "", text, flags=re.IGNORECASE)

    # Normalize spacing and preserve line breaks for display.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _render_safe_chat_html(content: str) -> str:
    """Escape chat text for HTML containers while preserving line breaks."""
    normalized = _normalize_chat_content(content)
    return html.escape(normalized).replace("\n", "<br>")


user_id = resolve_user_id()
remaining = remaining_quota(user_id)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div class="mi-sidebar-logo">🎙️ Meeting Intelligence</div>
        <div class="mi-sidebar-sub">AI transcription · summary · retrieval</div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload meeting audio/video (recommended)",
        type=["mp3", "mp4", "wav", "m4a", "webm", "mov", "mpeg"],
    )

    source = st.text_input(
        "Optional YouTube URL or local file path",
        placeholder="https://youtube.com/watch?v=...",
    )
    st.caption("YouTube URL processing is best-effort on shared cloud hosting. Uploads are most reliable.")

    language = st.selectbox(
        "Language",
        ["english", "hinglish"],
        index=0,
    )

    st.info(f"Remaining monthly queries: {remaining}/{MONTHLY_LIMIT}")
    if user_id.startswith("guest-"):
        st.caption("Guest session detected: quota is enforced per browser session.")

    run_btn = st.button("▶  Run Analysis", use_container_width=True)


# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="mi-page-title">AI Meeting Assistant</div>
    <div class="mi-page-sub">
        Transcripts · summaries · action items · decisions · contextual chat
    </div>
""", unsafe_allow_html=True)


# ── Pipeline ───────────────────────────────────────────────────────────────────
if run_btn:
    source = source.strip()
    if not uploaded_file and not source:
        st.error("Please upload a file or provide a valid YouTube URL/local file path.")
    else:
        reserved = reserve_quota(user_id)
        if not reserved:
            st.error(f"Monthly limit reached ({MONTHLY_LIMIT} requests).")
        else:
            try:
                with st.spinner("Processing meeting…"):
                    upload_name = uploaded_file.name if uploaded_file else None
                    upload_bytes = uploaded_file.getvalue() if uploaded_file else None
                    chunks       = process_input(
                        source=source,
                        uploaded_file_name=upload_name,
                        uploaded_file_bytes=upload_bytes,
                    )
                    transcript   = transcribe_all(chunks, language)
                    title        = generate_title(transcript)
                    summary      = summarize(transcript)
                    action_items = extract_action_items(transcript)
                    decisions    = extract_key_decisions(transcript)
                    questions    = extract_questions(transcript)
                    rag_chain    = build_rag_chain(transcript)

                st.session_state.result = {
                    "title":        title,
                    "summary":      summary,
                    "transcript":   transcript,
                    "action_items": action_items,
                    "decisions":    decisions,
                    "questions":    questions,
                    "rag_chain":    rag_chain,
                }
                st.session_state.chat_history = []
                commit_quota(user_id)
                st.success("Meeting processed successfully.")

            except Exception as e:
                release_quota(user_id)
                err = str(e)
                if source.startswith(("http://", "https://")) and "YouTube download failed" in err:
                    st.error(
                        "YouTube downloads may fail on cloud deployments due to "
                        "YouTube restrictions on shared server IPs. "
                        "Please upload the meeting file directly for reliable processing."
                    )
                else:
                    st.error(f"Processing failed: {err}")


# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.result:
    result = st.session_state.result

    # Meeting title card
    st.markdown(f"""
        <div class="mi-card">
            <div class="mi-card-title">Meeting Title</div>
            <div class="mi-meeting-title">{result["title"]}</div>
        </div>
    """, unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_overview, tab_actions, tab_decisions, tab_transcript, tab_chat = st.tabs([
        "Overview", "Action Items", "Decisions", "Transcript", "Chat"
    ])

    # ── Overview tab ───────────────────────────────────────────────────────────
    with tab_overview:
        # Summary
        st.markdown(f"""
            <div class="mi-card">
                <div class="mi-card-title">Executive Summary</div>
                <div style="font-size:0.9rem;color:#94a3b8;line-height:1.8;">
                    {result["summary"]}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Open questions
        st.markdown(f"""
            <div class="mi-card">
                <div class="mi-card-title">Open Questions</div>
                <div style="font-size:0.88rem;color:#94a3b8;line-height:1.8;">
                    {result["questions"]}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Action Items tab ───────────────────────────────────────────────────────
    with tab_actions:
        st.markdown(f"""
            <div class="mi-card">
                <div class="mi-card-title">Action Items</div>
                <div style="font-size:0.88rem;color:#94a3b8;line-height:1.9;">
                    {result["action_items"]}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Decisions tab ──────────────────────────────────────────────────────────
    with tab_decisions:
        st.markdown(f"""
            <div class="mi-card">
                <div class="mi-card-title">Key Decisions</div>
                <div style="font-size:0.88rem;color:#94a3b8;line-height:1.9;">
                    {result["decisions"]}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Transcript tab ─────────────────────────────────────────────────────────
    with tab_transcript:
        st.markdown(f"""
            <div class="mi-card">
                <div class="mi-card-title">Full Transcript</div>
                <div class="mi-transcript">{result["transcript"]}</div>
            </div>
        """, unsafe_allow_html=True)

    # ── Chat tab ───────────────────────────────────────────────────────────────
    with tab_chat:
        # Render history
        if st.session_state.chat_history:
            chat_html = '<div class="mi-chat-wrap">'
            for msg in st.session_state.chat_history:
                safe_content = _render_safe_chat_html(msg.get("content", ""))
                if msg["role"] == "user":
                    chat_html += f"""
                        <div class="mi-msg-user">
                            <div class="mi-sender">You</div>
                            {safe_content}
                        </div>
                    """
                else:
                    chat_html += f"""
                        <div class="mi-msg-ai">
                            <div class="mi-sender">Assistant</div>
                            {safe_content}
                        </div>
                    """
            chat_html += "</div>"
            st.markdown(chat_html, unsafe_allow_html=True)

        # Input row
        col_input, col_ask = st.columns([5, 1])
        with col_input:
            user_question = st.text_input(
                "question",
                label_visibility="collapsed",
                placeholder="Ask a question about the meeting…",
                key="chat_input",
            )
        with col_ask:
            ask_btn = st.button("Ask", use_container_width=True)

        if ask_btn and user_question.strip():
            reserved = reserve_quota(user_id)
            if not reserved:
                st.error(f"Monthly limit reached ({MONTHLY_LIMIT} requests).")
            else:
                try:
                    with st.spinner("Generating response…"):
                        response = ask_question(
                            result["rag_chain"],
                            user_question.strip(),
                        )
                    commit_quota(user_id)
                except Exception as e:
                    release_quota(user_id)
                    st.error(f"Request failed: {e}")
                else:
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_question.strip(),
                    })
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": _normalize_chat_content(response),
                    })
                    st.rerun()

        if st.session_state.chat_history:
            if st.button("Clear conversation"):
                st.session_state.chat_history = []
                st.rerun()

# ── Empty state ────────────────────────────────────────────────────────────────
else:
    st.markdown("""
        <div class="mi-empty">
            <div style="font-size:2.5rem;margin-bottom:1rem">🎙️</div>
            <div class="mi-empty-title">Upload meeting audio/video</div>
            <div class="mi-empty-sub">
                Upload a file from your device, or optionally provide a YouTube URL/local path in the sidebar
                to generate transcripts, summaries, action items and contextual chat.
            </div>
        </div>
    """, unsafe_allow_html=True)
