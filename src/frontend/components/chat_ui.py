"""Tampilan chat tanya-jawab ke pedoman WHO lewat endpoint /chat."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

API_DISCLAIMER = "⚠️ Ini bukan nasihat medis."
MAX_SUGGESTIONS = 3

GENERAL_QUESTIONS = [
    "Apa saja faktor risiko penyakit jantung?",
    "Bagaimana cara mencegah penyakit jantung?",
    "Berapa banyak aktivitas fisik yang disarankan?",
]


def suggested_questions(
    features: dict[str, float] | None,
    level: str | None,
    asked: set[str],
) -> list[str]:
    """Pilih pertanyaan siap-klik sesuai hasil cek risiko."""
    candidates: list[str] = []
    if features:
        if level == "tinggi":
            candidates.append("Pemeriksaan apa yang disarankan untuk orang dengan risiko penyakit jantung tinggi?")
        if features["trestbps"] >= 140:
            candidates.append("Bagaimana cara menurunkan tekanan darah tinggi?")
        if features["chol"] >= 240:
            candidates.append("Makanan apa yang disarankan untuk menurunkan kolesterol?")
        if features["fbs"] == 1:
            candidates.append("Apa hubungan gula darah tinggi dengan penyakit jantung?")
        if features["exang"] == 1:
            candidates.append("Kapan nyeri dada saat aktivitas perlu diperiksakan ke dokter?")
    candidates += GENERAL_QUESTIONS
    unique = [q for i, q in enumerate(candidates) if q not in candidates[:i] and q not in asked]
    return unique[:MAX_SUGGESTIONS]


def _merge_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Gabungkan sumber dari halaman yang sama dan urutkan per halaman."""
    by_page: dict[int, str] = {}
    for source in sources:
        page = source.get("page")
        if isinstance(page, int) and page not in by_page:
            by_page[page] = source.get("snippet", "")
    return [{"page": p, "snippet": by_page[p]} for p in sorted(by_page)]


def _split_disclaimer(answer: str) -> str:
    """Pisahkan disclaimer dari API agar ditampilkan dengan gaya seragam."""
    text = answer.strip()
    if text.endswith(API_DISCLAIMER):
        text = text[: -len(API_DISCLAIMER)].rstrip()
    return text


def _render_message(message: dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["content"])
            return
        st.markdown(message["content"])
        if message["role"] == "assistant":
            sources = message.get("sources", [])
            if sources:
                with st.expander(f"Sumber dari pedoman WHO 2007 ({len(sources)} halaman)"):
                    for source in sources:
                        snippet = source["snippet"].strip()
                        st.markdown(f"**Halaman {source['page']}** (halaman PDF)  \n_{snippet}…_")
            st.caption(API_DISCLAIMER)


def render_chat(
    ask_fn: Callable[[str], dict[str, Any]],
    error_cls: type[Exception],
    features: dict[str, float] | None = None,
    level: str | None = None,
) -> None:
    """Tampilkan riwayat chat, tombol pertanyaan siap-klik, dan kotak input."""
    messages: list[dict[str, Any]] = st.session_state.setdefault("messages", [])

    if not messages:
        st.caption(
            "Tanyakan hal seputar pencegahan penyakit jantung. Jawaban diambil dari "
            "pedoman WHO 2007 dan disertai nomor halaman sumbernya."
        )
    for message in messages:
        _render_message(message)

    asked = {m["content"] for m in messages if m["role"] == "user"}
    suggestions = suggested_questions(features, level, asked)
    if suggestions:
        st.markdown("**Pertanyaan yang mungkin membantu:**")
        for index, question in enumerate(suggestions):
            if st.button(question, key=f"saran_{index}_{question}"):
                st.session_state["pending_question"] = question
                st.rerun()

    typed = st.chat_input("Tulis pertanyaan kamu di sini…", max_chars=500)
    question = st.session_state.pop("pending_question", None) or typed
    if not question:
        return

    question = question.strip()
    if len(question) < 3:
        st.toast("Pertanyaan minimal 3 karakter.")
        return

    user_message = {"role": "user", "content": question}
    messages.append(user_message)
    _render_message(user_message)

    with st.spinner("Mencari jawaban di pedoman WHO…"):
        try:
            response = ask_fn(question)
            assistant_message = {
                "role": "assistant",
                "content": _split_disclaimer(response.get("answer", "")),
                "sources": _merge_sources(response.get("sources", [])),
            }
        except error_cls as exc:
            assistant_message = {"role": "assistant", "content": str(exc), "error": True}

    messages.append(assistant_message)
    st.rerun()
