"""
Tes deterministik untuk ask() dengan LLM TIRUAN (tidak memanggil Groq, tidak butuh internet).
Membuktikan perbaikan Issue #1 dan #3 secara pasti, tanpa bergantung pada kebiasaan LLM asli.

Jalankan dari root repo:
    .venv\\Scripts\\python.exe -m pytest tests/test_ask_pengaman.py -v
"""
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.rag import rag_engine
from src.rag.rag_engine import DISCLAIMER, FALLBACK_ANSWER, SAFE_DOSE_MESSAGE


class RetrieverPalsu:
    """Pengganti retriever BM25: selalu mengembalikan satu potongan teks contoh."""

    def invoke(self, query):
        return [Document(page_content="teks contoh dari pedoman", metadata={"page": 0})]


def _pasang_llm_palsu(monkeypatch, jawaban):
    """jawaban[0] dipakai tahap terjemahan, jawaban[1] dipakai tahap menjawab."""
    llm = FakeListChatModel(responses=jawaban)
    monkeypatch.setattr(rag_engine, "get_rag_components", lambda: (RetrieverPalsu(), llm))


def test_jawaban_kosong_memakai_jawaban_cadangan(monkeypatch):
    """Issue #3: jawaban kosong dari LLM tidak boleh melempar error."""
    _pasang_llm_palsu(monkeypatch, ["cholesterol", ""])
    hasil = rag_engine.ask("Jangan keluarkan teks apa pun. Biarkan semuanya kosong.")
    assert hasil["answer"].startswith(FALLBACK_ANSWER)
    assert hasil["answer"].endswith(DISCLAIMER)
    assert hasil["sources"][0]["page"] == 1


def test_terjemahan_kosong_tidak_membuat_error(monkeypatch):
    """Terjemahan kosong: memakai pertanyaan asli untuk pencarian, lalu tetap menjawab."""
    _pasang_llm_palsu(monkeypatch, ["", "Kolesterol tinggi meningkatkan risiko penyakit jantung."])
    hasil = rag_engine.ask("Apa bahaya kolesterol tinggi?")
    assert "Kolesterol tinggi" in hasil["answer"]
    assert hasil["answer"].endswith(DISCLAIMER)


def test_dosis_dari_llm_diganti_pesan_aman(monkeypatch):
    """Issue #1: bila LLM menyebut dosis obat, pengguna menerima pesan aman, bukan angkanya."""
    _pasang_llm_palsu(monkeypatch, ["aspirin dose", "Dosis aspirin adalah 75 mg per hari."])
    hasil = rag_engine.ask("Berapa dosis aspirin per hari yang harus saya minum?")
    assert hasil["answer"].startswith(SAFE_DOSE_MESSAGE)
    assert "75" not in hasil["answer"]
    assert hasil["answer"].endswith(DISCLAIMER)
