import os
import pickle
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def build_documents(pdf_path: str | Path | None = None) -> list[Document]:
    configured_path = pdf_path or os.getenv("PDF_PATH")
    if not configured_path:
        raise ValueError(
            "PDF_PATH belum diatur. Tambahkan lokasi PDF ke file .env atau "
            "berikan path saat memanggil build_documents()."
        )

    source_path = Path(configured_path).expanduser()
    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path
    if not source_path.is_file():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {source_path}")

    documents = PyPDFLoader(str(source_path)).load()
    cleaned_documents = []
    for doc in documents:
        page_num = doc.metadata.get("page", 0) + 1

        # Lewati halaman awal dan akhir yang umumnya berisi pengantar dan referensi.
        if page_num < 15 or page_num > len(documents) - 15:
            continue

        text = re.sub(r"\s+", " ", doc.page_content)
        if (
            "references" in text.lower()
            or "bibliography" in text.lower()
            or len(text.strip()) < 300
        ):
            continue

        doc.page_content = text
        cleaned_documents.append(doc)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(cleaned_documents)
    if not chunks:
        raise ValueError(
            "Tidak ada halaman yang dapat diindeks. Periksa PDF: proses ingest "
            "melewati 14 halaman awal dan 15 halaman akhir, serta mengabaikan "
            "halaman referensi atau teks yang kurang dari 300 karakter."
        )

    persist_file = PROJECT_ROOT / "vectorstore" / "docs.pkl"
    persist_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = persist_file.with_suffix(".pkl.tmp")
    with temporary_file.open("wb") as file:
        pickle.dump(chunks, file)
    temporary_file.replace(persist_file)

    print(f"Total halaman bersih: {len(cleaned_documents)}")
    print(f"Total potongan teks: {len(chunks)}")
    print(f"Dokumen berhasil disimpan di {persist_file}")
    return chunks


if __name__ == "__main__":
    build_documents()
