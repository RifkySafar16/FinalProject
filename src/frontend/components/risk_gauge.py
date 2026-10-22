"""Visualisasi hasil /predict: gauge, kategori warna, dan pesan untuk pengguna."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

# Ambang kategori (keputusan tim; bukan standar klinis).
LOW_MAX = 0.30
HIGH_MIN = 0.60

CATEGORIES = {
    "rendah": {
        "color": "#2E7D32",
        "text": "#FFFFFF",
        "message": (
            "Pola data kamu mirip kelompok dengan **risiko rendah**. Ini bukan jaminan "
            "bebas penyakit jantung. Tetap jaga gaya hidup sehat dan periksa kesehatan "
            "secara berkala."
        ),
    },
    "sedang": {
        "color": "#F9A825",
        "text": "#3E2723",
        "message": (
            "Pola data kamu mirip kelompok dengan **risiko sedang**. Sebaiknya "
            "konsultasikan hasil ini dengan dokter dan perhatikan faktor risiko yang "
            "masih bisa diubah."
        ),
    },
    "tinggi": {
        "color": "#C62828",
        "text": "#FFFFFF",
        "message": (
            "Pola data kamu mirip kelompok dengan **risiko tinggi**. Segera "
            "konsultasikan dengan dokter untuk pemeriksaan lebih lanjut."
        ),
    },
}


def categorize(probability: float) -> str:
    """Ubah probabilitas 0–1 menjadi 'rendah', 'sedang', atau 'tinggi'."""
    if probability < LOW_MAX:
        return "rendah"
    if probability <= HIGH_MIN:
        return "sedang"
    return "tinggi"


def build_gauge(probability: float) -> go.Figure:
    percent = round(probability * 100)
    level = categorize(probability)
    figure = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percent,
        number={"suffix": "%", "font": {"size": 44}},
        gauge={
            "axis": {"range": [0, 100], "tickvals": [0, 30, 60, 100]},
            "bar": {"color": CATEGORIES[level]["color"], "thickness": 0.3},
            "steps": [
                {"range": [0, LOW_MAX * 100], "color": "#E8F5E9"},
                {"range": [LOW_MAX * 100, HIGH_MIN * 100], "color": "#FFF8E1"},
                {"range": [HIGH_MIN * 100, 100], "color": "#FFEBEE"},
            ],
            "threshold": {
                "line": {"color": CATEGORIES[level]["color"], "width": 4},
                "thickness": 0.8,
                "value": percent,
            },
        },
    ))
    figure.update_layout(height=240, margin={"l": 30, "r": 30, "t": 30, "b": 10})
    return figure


def render_result(result: dict[str, Any], estimated: list[str]) -> None:
    probability = float(result["probability_presence"])
    level = categorize(probability)
    color = CATEGORIES[level]["color"]
    text_color = CATEGORIES[level]["text"]

    col_gauge, col_text = st.columns([1, 1.3])
    with col_gauge:
        st.plotly_chart(build_gauge(probability), config={"displayModeBar": False})
    with col_text:
        st.markdown(
            f"<div style='display:inline-block;padding:4px 14px;border-radius:999px;"
            f"background:{color};color:{text_color};font-weight:600;'>"
            f"Risiko {level.upper()}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(CATEGORIES[level]["message"])
        if estimated:
            st.info(
                "Hasil kurang akurat karena sebagian data diperkirakan: "
                + ", ".join(estimated) + "."
            )
        st.caption(
            "Angka ini adalah perkiraan model yang dilatih dari data 303 pasien "
            "rumah sakit (dataset Cleveland), bukan hasil diagnosis. "
            "Kategori: rendah < 30%, sedang 30–60%, tinggi > 60%."
        )
    st.warning(
        "⚠️ Ini bukan nasihat medis. Konsultasikan hasil ini dengan dokter.",
    )
