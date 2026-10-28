"""Penghubung frontend ke backend FastAPI (endpoint /predict dan /chat).

Alamat backend diambil dari variabel lingkungan API_URL
(default: http://127.0.0.1:8000). Set FRONTEND_MOCK=1 untuk mencoba
tampilan tanpa backend atau tanpa GROQ_API_KEY.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
USE_MOCK = os.getenv("FRONTEND_MOCK", "0") == "1"

PREDICT_TIMEOUT = 15  # detik
CHAT_TIMEOUT = 90  # detik; /chat memanggil LLM dua kali


class ApiError(Exception):
    """Kesalahan yang pesannya aman ditampilkan ke pengguna."""


def check_backend() -> bool:
    """True bila server backend bisa dihubungi."""
    if USE_MOCK:
        return True
    try:
        response = requests.get(f"{API_URL}/openapi.json", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def predict(features: dict[str, float]) -> dict[str, Any]:
    """Kirim 13 fitur ke /predict.

    Hasil: {"risk_level": "low"|"moderate"|"high", "score": int,
            "max_score": int, "factors": [...], "disclaimer": str}
    """
    if USE_MOCK:
        return _mock_predict(features)
    return _post("/predict", features, PREDICT_TIMEOUT)


def ask(question: str) -> dict[str, Any]:
    """Kirim pertanyaan ke /chat.

    Hasil: {"answer": str, "sources": [{"page": int, "snippet": str}, ...]}
    """
    if USE_MOCK:
        return _mock_ask(question)
    return _post("/chat", {"question": question}, CHAT_TIMEOUT)


def _post(path: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    try:
        response = requests.post(f"{API_URL}{path}", json=payload, timeout=timeout)
    except requests.ConnectionError as exc:
        raise ApiError(
            "Server backend belum menyala atau alamatnya salah. "
            f"Pastikan API berjalan di {API_URL}."
        ) from exc
    except requests.Timeout as exc:
        raise ApiError("Server terlalu lama merespons. Silakan coba lagi.") from exc

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError("Jawaban server tidak dapat dibaca.") from exc

    detail = _read_detail(response)
    if response.status_code == 422:
        raise ApiError(f"Data yang dikirim belum sesuai: {detail}")
    if response.status_code == 503:
        raise ApiError(detail or "Layanan belum siap. Coba lagi nanti.")
    raise ApiError(
        "Layanan sedang bermasalah. Silakan coba beberapa saat lagi. "
        f"(kode {response.status_code})"
    )


def _read_detail(response: requests.Response) -> str:
    """Ambil pesan 'detail' dari respons error FastAPI, bila ada."""
    try:
        detail = response.json().get("detail", "")
    except ValueError:
        return ""
    if isinstance(detail, list):  # error validasi Pydantic
        parts = []
        for item in detail:
            field = item.get("loc", ["", ""])[-1]
            parts.append(f"{field}: {item.get('msg', '')}")
        return "; ".join(parts)
    return str(detail)


# ---------------------------------------------------------------------------
# Mode contoh (FRONTEND_MOCK=1): jawaban palsu untuk mencoba tampilan
# ---------------------------------------------------------------------------

def _mock_predict(features: dict[str, float]) -> dict[str, Any]:
    factors = []
    if features["age"] >= 45:
        factors.append({"feature": "age", "value": features["age"], "points": 2,
                        "reason": "usia 45 tahun ke atas (contoh)"})
    if features["trestbps"] >= 130:
        factors.append({"feature": "trestbps", "value": features["trestbps"],
                        "points": 6, "reason": "tekanan darah tinggi (contoh)"})
    if features["chol"] >= 240:
        factors.append({"feature": "chol", "value": features["chol"], "points": 2,
                        "reason": "kolesterol tinggi (contoh)"})
    if features["exang"] == 1:
        factors.append({"feature": "exang", "value": 1.0, "points": 4,
                        "reason": "ada nyeri dada saat olahraga (contoh)"})
    score = sum(f["points"] for f in factors)
    level = "low" if score <= 10 else "moderate" if score <= 22 else "high"
    return {
        "risk_level": level,
        "score": score,
        "max_score": 41,
        "factors": factors,
        "disclaimer": "Mode contoh: skor ini bukan hasil perhitungan asli.",
    }


def _mock_ask(question: str) -> dict[str, Any]:
    return {
        "answer": (
            f"(Mode contoh) Ini adalah jawaban contoh untuk pertanyaan: "
            f"\"{question}\". Jawaban asli berasal dari pedoman WHO 2007. "
            "⚠️ Ini bukan nasihat medis."
        ),
        "sources": [
            {"page": 30, "snippet": "Contoh potongan teks dari pedoman"},
            {"page": 30, "snippet": "Potongan lain dari halaman yang sama"},
            {"page": 44, "snippet": "Contoh potongan teks dari halaman lain"},
        ],
    }
