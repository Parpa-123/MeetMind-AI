from utils.audio_processor import process_input
from dotenv import load_dotenv
from utils.runtime_setup import configure_runtime
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_questions,
    extract_key_decisions,
)

configure_runtime()
from core.rag_engine import build_rag_chain, ask_question
load_dotenv()


def run_pipeline(source: str, language: str = "english") -> dict:
    print("Start AI Video Assistant")

    chunks = process_input(source)
    transcript = transcribe_all(chunks, language)

    print(f"Raw transcription (first 300 characters): {transcript[:300]}")

    title = generate_title(transcript)
    summary = summarize(transcript)
    action_item = extract_action_items(transcript)
    decision = extract_key_decisions(transcript)
    question = extract_questions(transcript)

    rag_chain = build_rag_chain(transcript)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decision,
        "open_questions": question,
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"

    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"Title: {result['title']}")
    print(f"\nSummary:\n{result['summary']}")
    print(f"\nAction Items:\n{result['action_items']}")
    print(f"\nKey Decisions:\n{result['key_decisions']}")
    print(f"\nOpen Questions:\n{result['open_questions']}")
    print("=" * 60)

    print("\nChat with your meeting (type 'exit' to quit)\n")

    rag_chain = result["rag_chain"]

    while True:
        question = input("You: ").strip()

        if question.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break

        if not question:
            continue

        answer = ask_question(rag_chain, question)

        print(f"\nAssistant: {answer}\n")
