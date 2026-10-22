"""Heart Risk Advisor — antarmuka Streamlit (Orang 4: Frontend).

Jalankan dari root repository (backend harus sudah menyala):
    streamlit run src/frontend/app.py

Variabel lingkungan (opsional, bisa di file .env):
    API_URL=http://127.0.0.1:8000   alamat backend FastAPI
    FRONTEND_MOCK=1                 coba tampilan tanpa backend
"""

from __future__ import annotations

import sys
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

import streamlit as st  # noqa: E402

import api_client  # noqa: E402
from components.chat_ui import render_chat  # noqa: E402
from components.form_input import render_form  # noqa: E402
from components.risk_gauge import categorize, render_result  # noqa: E402

LOGO_PATH = FRONTEND_DIR / "assets" / "logo.png"

st.set_page_config(
    page_title="Heart Risk Advisor",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "❤️",
    layout="wide",
)

# ---------------------------------------------------------------- Header
col_logo, col_title = st.columns([1, 11])
with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=72)
with col_title:
    st.title("Heart Risk Advisor")
    st.caption(
        "Cek perkiraan risiko penyakit jantung dan tanya pedoman WHO 2007 "
        "dengan bahasa sederhana."
    )

st.warning(
    "**Disclaimer medis:** aplikasi ini hanya untuk edukasi, bukan pengganti "
    "diagnosis atau saran dokter. Jangan memulai, mengubah, atau menghentikan "
    "pengobatan berdasarkan hasil aplikasi ini."
)

# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.error(
        "**Darurat?** Nyeri dada hebat, sesak napas berat, atau lemah separuh "
        "badan: segera ke IGD atau hubungi **119**."
    )
    if api_client.USE_MOCK:
        st.info("Mode contoh aktif: data dan jawaban bukan dari model asli.")
    elif api_client.check_backend():
        st.success("Server terhubung")
    else:
        st.error(f"Server tidak terhubung ({api_client.API_URL})")

    st.header("Cek Risiko")
    submission = render_form()

# ---------------------------------------------------------------- Hasil risiko
if submission is not None:
    features, estimated = submission
    with st.spinner("Menghitung perkiraan risiko…"):
        try:
            st.session_state["result"] = api_client.predict(features)
            st.session_state["features"] = features
            st.session_state["estimated"] = estimated
            st.session_state.pop("predict_error", None)
        except api_client.ApiError as exc:
            st.session_state["predict_error"] = str(exc)
            st.session_state.pop("result", None)

st.subheader("Hasil Cek Risiko")
if "predict_error" in st.session_state:
    st.error(st.session_state["predict_error"])
elif "result" in st.session_state:
    render_result(st.session_state["result"], st.session_state.get("estimated", []))
else:
    st.info("Isi data di panel kiri, lalu tekan **Cek Risiko**.")

# ---------------------------------------------------------------- Chat
st.divider()
col_head, col_clear = st.columns([5, 1])
with col_head:
    st.subheader("Tanya Pedoman WHO")
with col_clear:
    if st.button("Hapus percakapan", disabled=not st.session_state.get("messages")):
        st.session_state["messages"] = []
        st.rerun()

result = st.session_state.get("result")
render_chat(
    api_client.ask,
    api_client.ApiError,
    features=st.session_state.get("features") if result else None,
    level=categorize(result["probability_presence"]) if result else None,
)
