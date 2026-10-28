"""Visualisasi hasil /predict: gauge skor, kategori warna, faktor, dan pesan.

Format respons /predict (skor heuristik berbasis aturan, src/ml/risk.py):
    {"risk_level": "low"|"moderate"|"high", "score": int, "max_score": int,
     "factors": [{"feature": str, "value": float, "points": int, "reason": str}],
     "disclaimer": str}
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import streamlit as st

# Batas kategori skor, disamakan dengan RISK_SCORE_THRESHOLDS di src/ml/risk.py.
LOW_MAX = 10
HIGH_MIN = 23

LEVEL_NAMES = {"low": "rendah", "moderate": "sedang", "high": "tinggi"}

FEATURE_LABELS = {
    "age": "Usia",
    "sex": "Jenis kelamin",
    "cp": "Keluhan nyeri dada",
    "trestbps": "Tekanan darah",
    "chol": "Kolesterol",
    "fbs": "Gula darah puasa",
    "restecg": "Hasil EKG istirahat",
    "thalach": "Detak jantung maksimum",
    "exang": "Nyeri dada saat olahraga",
    "oldpeak": "Penurunan segmen ST",
    "slope": "Kemiringan segmen ST",
    "ca": "Pembuluh darah terwarnai",
    "thal": "Hasil tes thalium",
}

CATEGORIES = {
    "rendah": {
        "color": "#2E7D32",
        "text": "#FFFFFF",
        "message": (
            "Skor kamu masuk kategori **risiko rendah**. Ini bukan jaminan bebas "
            "penyakit jantung. Tetap jaga gaya hidup sehat dan periksa kesehatan "
            "secara berkala."
        ),
    },
    "sedang": {
        "color": "#F9A825",
        "text": "#3E2723",
        "message": (
            "Skor kamu masuk kategori **risiko sedang**. Sebaiknya konsultasikan "
            "hasil ini dengan dokter dan perhatikan faktor risiko yang masih bisa "
            "diubah."
        ),
    },
    "tinggi": {
        "color": "#C62828",
        "text": "#FFFFFF",
        "message": (
            "Skor kamu masuk kategori **risiko tinggi**. Segera konsultasikan "
            "dengan dokter untuk pemeriksaan lebih lanjut."
        ),
    },
}


def categorize(result: dict[str, Any]) -> str:
    """Ubah risk_level dari API ('low'/'moderate'/'high') menjadi nama Indonesia."""
    return LEVEL_NAMES.get(str(result.get("risk_level")), "sedang")


def build_gauge(score: int, max_score: int, level: str) -> go.Figure:
    color = CATEGORIES[level]["color"]
    figure = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": f" / {max_score}", "font": {"size": 40}},
        gauge={
            "axis": {"range": [0, max_score],
                     "tickvals": [0, LOW_MAX, HIGH_MIN, max_score]},
            "bar": {"color": color, "thickness": 0.3},
            "steps": [
                {"range": [0, LOW_MAX + 0.5], "color": "#E8F5E9"},
                {"range": [LOW_MAX + 0.5, HIGH_MIN - 0.5], "color": "#FFF8E1"},
                {"range": [HIGH_MIN - 0.5, max_score], "color": "#FFEBEE"},
            ],
            "threshold": {
                "line": {"color": color, "width": 4},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    figure.update_layout(height=240, margin={"l": 30, "r": 30, "t": 30, "b": 10})
    return figure


def _render_factors(factors: list[dict[str, Any]]) -> None:
    if not factors:
        st.markdown("Tidak ada faktor yang menambah skor.")
        return
    ordered = sorted(factors, key=lambda f: f.get("points", 0), reverse=True)
    with st.expander(f"Faktor yang menambah skor ({len(ordered)})", expanded=True):
        lines = []
        for factor in ordered:
            label = FEATURE_LABELS.get(factor.get("feature", ""), factor.get("feature", ""))
            reason = factor.get("reason") or ""
            lines.append(f"- **{label}** (+{factor.get('points', 0)}): {reason}")
        st.markdown("\n".join(lines))


def render_result(result: dict[str, Any], estimated: list[str]) -> None:
    score = int(result["score"])
    max_score = int(result["max_score"])
    level = categorize(result)
    color = CATEGORIES[level]["color"]
    text_color = CATEGORIES[level]["text"]

    col_gauge, col_text = st.columns([1, 1.3])
    with col_gauge:
        st.plotly_chart(build_gauge(score, max_score, level),
                        config={"displayModeBar": False})
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
            f"Skor dihitung dari 13 faktor dengan aturan sederhana (maksimal "
            f"{max_score} poin). Kategori: rendah 0–{LOW_MAX}, sedang "
            f"{LOW_MAX + 1}–{HIGH_MIN - 1}, tinggi ≥ {HIGH_MIN}."
        )
    _render_factors(result.get("factors", []))
    st.warning(
        "⚠️ " + (result.get("disclaimer")
                 or "Ini bukan nasihat medis. Konsultasikan hasil ini dengan dokter."),
    )
