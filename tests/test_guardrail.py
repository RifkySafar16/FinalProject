"""
Tes unit untuk pengaman keluaran (_terapkan_pengaman) di src/rag/rag_engine.py.
Tidak memanggil LLM, jadi hasilnya selalu sama dan cepat (hitungan detik).

Jalankan dari root repo:
    .venv\\Scripts\\python.exe -m pytest tests/test_guardrail.py -v
"""
import pytest

from src.rag.rag_engine import (
    DISCLAIMER,
    SAFE_DOSE_MESSAGE,
    SAFE_SHORT_MESSAGE,
    _terapkan_pengaman,
)


@pytest.mark.parametrize("pertanyaan,jawaban", [
    ("Berapa dosis aspirin per hari?", "Dosis aspirin yang disarankan adalah 75 mg sekali sehari."),
    ("Berapa dosis aspirin per hari?", "Dosisnya adalah 75 mg per hari."),
    ("Apakah parasetamol menyembuhkan darah tinggi?", "Minum 10 tablet sekaligus tidak dianjurkan."),
    ("Obat apa yang harus saya minum?", "Aspirin 100 miligram setiap hari."),
])
def test_dosis_obat_diganti_pesan_aman(pertanyaan, jawaban):
    assert _terapkan_pengaman(pertanyaan, jawaban) == SAFE_DOSE_MESSAGE


@pytest.mark.parametrize("jawaban", ["Tidak", "Ya.", f"Tidak {DISCLAIMER}", "  Ya  "])
def test_jawaban_satu_kata_diganti_penjelasan(jawaban):
    hasil = _terapkan_pengaman("Apakah saya pasti sakit jantung?", jawaban)
    assert hasil == SAFE_SHORT_MESSAGE
    assert "dokter" in hasil


@pytest.mark.parametrize("pertanyaan,jawaban", [
    ("Berapa kolesterol yang baik?", "Kolesterol total sebaiknya di bawah 190 mg/dl."),
    ("Berapa LDL yang baik?", "LDL sebaiknya kurang dari 115 mg/dl atau 3,0 mmol/l."),
    ("Berapa batas garam per hari?", "Batasi garam kurang dari 5 gram per hari."),
    ("Jelaskan kolesterol", "Mengurangi asupan kolesterol makanan sebesar 100 mg per hari menurunkan kolesterol darah sekitar 1 persen."),
    ("Siapa presiden pertama Indonesia?", "Maaf, informasi tidak ditemukan."),
])
def test_jawaban_wajar_tidak_diubah(pertanyaan, jawaban):
    """Pengaman tidak boleh memblokir jawaban edukasi yang sah (hasil lab, garam, dll)."""
    assert _terapkan_pengaman(pertanyaan, jawaban) is jawaban


def test_jawaban_dengan_disclaimer_tidak_diubah():
    jawaban = f"Aktivitas fisik membantu menjaga kesehatan jantung. {DISCLAIMER}"
    assert _terapkan_pengaman("Apa manfaat olahraga?", jawaban) == jawaban
