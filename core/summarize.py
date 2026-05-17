from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import os

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        temperature=0.2,
        max_tokens=2048,
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
    )

def split_transcript(transcript: str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
    )
    return text_splitter.split_text(transcript)

def summarize(transcript : str) -> str:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes transcripts of meetings."),
        ("human", "Summarize the following transcript:\n\n{transcript}"),
    ])

    rag_chain = prompt | llm | StrOutputParser()

    chunks = split_transcript(transcript)

    chunk_summaries = [rag_chain.invoke({"transcript" : chunk}) for chunk in chunks]
    combined = "\n\n".join(chunk_summaries)
    combined_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes transcripts of meetings."),
        ("human", "Summarize the following summaries of meeting transcript chunks into a single summary:\n\n{combined}"),
    ])
    combined_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"combined": x}) | combined_prompt | llm | StrOutputParser()
    )
    final_summary = combined_chain.invoke({"combined" : combined})
    return final_summary


def generate_title(transcript: str) -> str:
    llm = get_llm()



    title_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x: {"combined": x}) | ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that generates concise titles for meetings based on their transcripts."),
            ("human", "Generate a concise title for a meeting with the following transcript:\n\n{combined}"),
        ]) | llm | StrOutputParser()
    )
    
    return title_chain.invoke({"combined" : transcript[0:2000]})

