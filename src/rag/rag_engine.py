import os
import pickle
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from src.rag.prompts import RAG_PROMPT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_FILE = PROJECT_ROOT / "vectorstore" / "docs.pkl"
DISCLAIMER = "⚠️ Ini bukan nasihat medis."

load_dotenv(PROJECT_ROOT / ".env")

TRANSLATE_PROMPT = PromptTemplate(
    input_variables=["question"],
    template=(
        "Translate the following Indonesian health question into English "
        "keywords. Only output the English translation, nothing else.\n"
        "Question: {question}\nEnglish:"
    ),
)


class Source(TypedDict):
    page: int
    snippet: str


class AskResponse(TypedDict):
    answer: str
    sources: list[Source]


@lru_cache(maxsize=1)
def get_rag_components() -> tuple[BM25Retriever, ChatGroq]:
    if not DOCS_FILE.is_file():
        raise FileNotFoundError(
            f"File indeks tidak ditemukan: {DOCS_FILE}. "
            "Jalankan `python3 src/rag/ingest.py` terlebih dahulu."
        )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY belum diatur di file .env.")

    with DOCS_FILE.open("rb") as file:
        chunks = pickle.load(file)
    if not chunks:
        raise ValueError(f"File indeks tidak berisi dokumen: {DOCS_FILE}")

    retriever = BM25Retriever.from_documents(chunks)
    retriever.k = 8

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=api_key,
        temperature=0,
    )
    return retriever, llm


def ask(question: str) -> AskResponse:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    retriever, llm = get_rag_components()

    translate_chain = TRANSLATE_PROMPT | llm | StrOutputParser()
    english_query = translate_chain.invoke({"question": question}).strip()
    if not english_query:
        raise RuntimeError("Model tidak menghasilkan terjemahan pertanyaan.")

    source_documents = retriever.invoke(english_query)
    answer_chain = RAG_PROMPT | llm | StrOutputParser()
    answer = answer_chain.invoke(
        {
            "context": "\n\n".join(doc.page_content for doc in source_documents),
            "question": question.strip(),
        }
    ).strip()
    if not answer:
        raise RuntimeError("Model tidak menghasilkan jawaban.")
    if not answer.endswith(DISCLAIMER):
        answer = f"{answer} {DISCLAIMER}"

    sources: list[Source] = []
    for doc in source_documents:
        page_index = doc.metadata.get("page")
        if not isinstance(page_index, int) or isinstance(page_index, bool) or page_index < 0:
            raise ValueError("Dokumen sumber tidak memiliki metadata nomor halaman PDF.")
        sources.append(
            {
                "page": page_index + 1,
                "snippet": doc.page_content[:200],
            }
        )

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    response = ask("Apa arti kolesterol tinggi menurut panduan ini?")
    print("\n--- JAWABAN AI ---")
    print(response["answer"])
    print("\n--- SUMBER ---")
    for source in response["sources"]:
        print(f"Halaman {source['page']}: {source['snippet']}...")
