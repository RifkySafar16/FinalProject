"""Peluncur Heart Risk Advisor untuk Streamlit Community Cloud.

Streamlit Community Cloud hanya menjalankan satu aplikasi Streamlit, jadi file ini:
  1. Menyalin kunci GROQ_API_KEY dari Secrets ke environment.
  2. Menyiapkan PDF WHO, melatih model, dan membuat indeks RAG (sekali per server).
  3. Menyalakan backend FastAPI di 127.0.0.1:8000 (proses latar).
  4. Menjalankan frontend src/frontend/app.py.

Pengaturan di Streamlit Community Cloud:
  Main file path : deploy/streamlit_cloud/streamlit_app.py
  Python version : 3.12
  Secrets        : GROQ_API_KEY = "gsk_..."

Bisa juga dicoba di komputer sendiri (dari root repo):
  python -m streamlit run deploy/streamlit_cloud/streamlit_app.py
"""

from __future__ import annotations

import os
import runpy
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
PDF_SOURCE = ROOT / "deploy" / "who_cvd_guideline_2007.pdf"
PDF_TARGET = ROOT / "data" / "raw" / "who_cvd_guideline_2007.pdf"
MODEL_FILE = ROOT / "models" / "heart_model.pkl"
INDEX_FILE = ROOT / "vectorstore" / "docs.pkl"
BACKEND_URL = "http://127.0.0.1:8000"


def _load_secrets() -> None:
    """Salin GROQ_API_KEY dari Secrets Streamlit ke variabel lingkungan."""
    if os.getenv("GROQ_API_KEY"):
        return
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:  # file secrets tidak ada saat dijalankan lokal
        key = None
    if key:
        os.environ["GROQ_API_KEY"] = str(key)


def _backend_alive() -> bool:
    try:
        return requests.get(f"{BACKEND_URL}/openapi.json", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def _run_step(args: list[str], env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        [sys.executable, *args], cwd=ROOT, env=env,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Langkah {' '.join(args)} gagal:\n{result.stderr[-2000:]}"
        )


@st.cache_resource(show_spinner=False)
def prepare_and_start_backend() -> bool:
    """Siapkan model + indeks, lalu nyalakan backend. Berjalan sekali per server."""
    if not PDF_TARGET.exists():
        PDF_TARGET.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PDF_SOURCE, PDF_TARGET)

    if not MODEL_FILE.exists():
        _run_step(["-m", "src.ml.train"])

    if not INDEX_FILE.exists():
        env = {**os.environ, "PDF_PATH": str(PDF_TARGET)}
        _run_step(["src/rag/ingest.py"], env=env)

    if not _backend_alive():
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.backend.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT, env={**os.environ},
        )
        for _ in range(90):
            if _backend_alive():
                break
            time.sleep(1)
    return _backend_alive()


_load_secrets()
os.environ.setdefault("API_URL", BACKEND_URL)

with st.spinner(
    "Menyiapkan aplikasi (hanya saat server baru menyala, sekitar 1–3 menit)…"
):
    prepare_and_start_backend()

runpy.run_path(str(ROOT / "src" / "frontend" / "app.py"), run_name="__main__")
