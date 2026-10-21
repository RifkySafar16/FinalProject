import pickle

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from src.rag import ingest, rag_engine


def test_ask_returns_indonesian_answer_disclaimer_and_one_based_sources(monkeypatch):
    class FakeRetriever:
        def invoke(self, query):
            assert query == "high cholesterol"
            return [
                Document(
                    page_content="Information about cholesterol.",
                    metadata={"page": 83},
                )
            ]

    def fake_model(prompt):
        prompt_text = prompt.to_string()
        if prompt_text.startswith("Translate"):
            return AIMessage(content="high cholesterol")
        return AIMessage(content="Kolesterol tinggi meningkatkan risiko.")

    monkeypatch.setattr(
        rag_engine,
        "get_rag_components",
        lambda: (FakeRetriever(), RunnableLambda(fake_model)),
    )

    response = rag_engine.ask("Apa itu kolesterol tinggi?")

    assert response == {
        "answer": "Kolesterol tinggi meningkatkan risiko. "
        "⚠️ Ini bukan nasihat medis.",
        "sources": [
            {
                "page": 84,
                "snippet": "Information about cholesterol.",
            }
        ],
    }


def test_ask_rejects_empty_question(monkeypatch):
    monkeypatch.setattr(
        rag_engine,
        "get_rag_components",
        lambda: pytest.fail("RAG components should not be loaded"),
    )

    with pytest.raises(ValueError, match="tidak boleh kosong"):
        rag_engine.ask("  ")


def test_build_documents_uses_repository_root_and_preserves_pdf_pages(
    tmp_path, monkeypatch
):
    pdf_path = tmp_path / "guide.pdf"
    pdf_path.touch()
    monkeypatch.setattr(ingest, "PROJECT_ROOT", tmp_path)

    class FakePDFLoader:
        def __init__(self, path):
            assert path == str(pdf_path)

        def load(self):
            return [
                Document(
                    page_content=f"Page {page_index}. " + ("Health information. " * 25),
                    metadata={"page": page_index},
                )
                for page_index in range(40)
            ]

    monkeypatch.setattr(ingest, "PyPDFLoader", FakePDFLoader)

    chunks = ingest.build_documents(pdf_path)
    index_path = tmp_path / "vectorstore" / "docs.pkl"

    assert index_path.is_file()
    with index_path.open("rb") as file:
        saved_chunks = pickle.load(file)
    assert [chunk.metadata["page"] for chunk in chunks] == list(range(14, 25))
    assert len(saved_chunks) == len(chunks)


def test_build_documents_requires_pdf_path(monkeypatch):
    monkeypatch.delenv("PDF_PATH", raising=False)

    with pytest.raises(ValueError, match="PDF_PATH belum diatur"):
        ingest.build_documents()
