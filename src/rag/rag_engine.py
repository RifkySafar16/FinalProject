import os
import pickle
import re
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

# --- Pengaman keluaran (output guardrail) -----------------------------------
# Perbaikan untuk temuan uji keamanan QA (Issue #1, #2, #3 di GitHub).
FALLBACK_ANSWER = "Maaf, informasi tidak ditemukan."
SAFE_DOSE_MESSAGE = (
    "Maaf, aplikasi ini tidak dapat memberikan dosis atau anjuran penggunaan obat. "
    "Dosis dan penggunaan obat harus ditentukan oleh dokter atau apoteker setelah pemeriksaan."
)
SAFE_SHORT_MESSAGE = (
    "Maaf, pertanyaan kesehatan tidak dapat dijawab hanya dengan satu kata. "
    "Silakan konsultasikan kondisi Anda dengan dokter atau tenaga kesehatan."
)
# Angka + satuan obat. Satuan hasil lab seperti "190 mg/dl" sengaja dikecualikan.
DOSE_PATTERN = re.compile(
    r"\d+(?:[.,]\d+)?\s?(?:mg|miligram|mcg|mikrogram|tablet|kapsul)\b(?!\s*/\s*(?:dl|l)\b)",
    re.IGNORECASE,
)
# Kata yang menandakan konteks obat. Pengaman hanya aktif jika angka dosis DAN konteks obat ada.
DRUG_CONTEXT = re.compile(
    r"\b(?:dosis|aspirin|obat|statin|tablet|kapsul|minum|diminum|resep)\w*",
    re.IGNORECASE,
)

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


def _terapkan_pengaman(question: str, answer: str) -> str:
    """Periksa jawaban LLM sebelum dikirim ke pengguna.

    - Jawaban hanya satu kata (mis. "Tidak") diganti penjelasan yang merujuk ke dokter.
    - Jawaban yang memuat angka dosis obat diganti pesan aman.
    Jawaban lain dikembalikan apa adanya.
    """
    teks = answer.replace(DISCLAIMER, "").strip()
    if len(teks.split()) < 2:
        return SAFE_SHORT_MESSAGE
    if DOSE_PATTERN.search(teks) and DRUG_CONTEXT.search(f"{question} {teks}"):
        return SAFE_DOSE_MESSAGE
    return answer


def ask(question: str) -> AskResponse:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Pertanyaan tidak boleh kosong.")

    retriever, llm = get_rag_components()

    translate_chain = TRANSLATE_PROMPT | llm | StrOutputParser()
    english_query = translate_chain.invoke({"question": question}).strip()
    if not english_query:
        # Cadangan: pakai pertanyaan asli bila terjemahan kosong (sebelumnya melempar error).
        english_query = question.strip()

    source_documents = retriever.invoke(english_query)
    answer_chain = RAG_PROMPT | llm | StrOutputParser()
    answer = answer_chain.invoke(
        {
            "context": "\n\n".join(doc.page_content for doc in source_documents),
            "question": question.strip(),
        }
    ).strip()
    if not answer:
        # Sebelumnya melempar RuntimeError (Issue #3); sekarang memakai jawaban cadangan.
        answer = FALLBACK_ANSWER
    answer = _terapkan_pengaman(question, answer)
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
