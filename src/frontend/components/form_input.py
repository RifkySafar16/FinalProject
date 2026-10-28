"""Form data kesehatan untuk endpoint /predict.

Skor risiko dihitung dari 13 faktor, dan SEMUA faktor wajib diisi pengguna:
7 data dasar dan 6 data klinis dari hasil pemeriksaan jantung. Tidak ada
nilai bawaan; form menolak dikirim selama masih ada isian yang kosong.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

CHEST_PAIN_OPTIONS: dict[int, str] = {
    4: "Tidak ada nyeri dada",
    1: "Nyeri dada khas",
    2: "Nyeri dada tidak khas",
    3: "Nyeri bukan dari jantung",
}
CHEST_PAIN_HELP = (
    "Nyeri dada khas: terasa menekan, muncul saat aktivitas, reda saat istirahat. "
    "Tidak khas: hanya sebagian ciri tersebut. "
    "Bukan dari jantung: misalnya nyeri otot atau lambung."
)

RESTECG_OPTIONS = {
    0: "Normal",
    1: "Ada kelainan gelombang ST-T",
    2: "Penebalan otot jantung kiri (LVH)",
}
SLOPE_OPTIONS = {
    1: "Naik (upsloping)",
    2: "Datar (flat)",
    3: "Turun (downsloping)",
}
CA_OPTIONS = {
    0: "0 pembuluh",
    1: "1 pembuluh",
    2: "2 pembuluh",
    3: "3 pembuluh",
}
THAL_OPTIONS = {
    3: "Normal",
    6: "Kelainan menetap (fixed defect)",
    7: "Kelainan yang dapat pulih (reversible defect)",
}

PLACEHOLDER = "Pilih salah satu"

# Nama isian untuk pesan "belum diisi", sesuai urutan tampil di form.
FIELD_LABELS = {
    "age": "Usia",
    "sex": "Jenis kelamin",
    "trestbps": "Tekanan darah",
    "chol": "Kolesterol total",
    "fbs": "Gula darah puasa",
    "cp": "Keluhan nyeri dada",
    "exang": "Nyeri dada saat olahraga",
    "restecg": "Hasil EKG saat istirahat",
    "thalach": "Detak jantung maksimum",
    "oldpeak": "Penurunan segmen ST",
    "slope": "Kemiringan segmen ST",
    "ca": "Jumlah pembuluh darah (fluoroskopi)",
    "thal": "Hasil tes thalium",
}


def _choice(label: str, options: dict[int, str], help_text: str | None = None) -> int | None:
    return st.selectbox(
        label, list(options), index=None, placeholder=PLACEHOLDER,
        format_func=options.get, help=help_text,
    )


def _yes_no(label: str) -> float | None:
    answer = st.radio(label, ["Tidak", "Ya"], index=None, horizontal=True)
    if answer is None:
        return None
    return 1.0 if answer == "Ya" else 0.0


def render_form() -> tuple[dict[str, float], list[str]] | None:
    """Tampilkan form. Kembalikan (fitur, []) saat dikirim dan semua isian lengkap."""
    with st.form("form_risiko"):
        st.caption("Semua isian **wajib** diisi.")
        st.subheader("Data dasar")

        values: dict[str, Any] = {}
        values["age"] = st.number_input(
            "Usia (tahun)", min_value=18, max_value=100, value=None, step=1,
            placeholder="Contoh: 50",
            help="Data acuan (dataset Cleveland) berisi pasien berusia 29–77 tahun.",
        )
        sex = st.radio(
            "Jenis kelamin", ["Laki-laki", "Perempuan"], index=None, horizontal=True,
        )
        values["sex"] = None if sex is None else (1.0 if sex == "Laki-laki" else 0.0)
        values["trestbps"] = st.number_input(
            "Tekanan darah atas / sistolik (mmHg)",
            min_value=80, max_value=220, value=None, step=1, placeholder="Contoh: 120",
            help="Angka pertama hasil tensi. Contoh: tensi 120/80 → isi 120.",
        )
        values["chol"] = st.number_input(
            "Kolesterol total (mg/dl)",
            min_value=100, max_value=600, value=None, step=1, placeholder="Contoh: 200",
            help="Bila hasil lab dalam mmol/l, kalikan 38,67. Contoh: 5,2 mmol/l ≈ 201 mg/dl.",
        )
        values["fbs"] = _yes_no("Gula darah puasa di atas 120 mg/dl?")
        values["cp"] = _choice("Keluhan nyeri dada", CHEST_PAIN_OPTIONS, CHEST_PAIN_HELP)
        values["exang"] = _yes_no("Nyeri dada saat olahraga atau aktivitas berat?")

        st.subheader("Data klinis")
        st.caption(
            "Diambil dari hasil pemeriksaan jantung: EKG, uji latih jantung "
            "(treadmill), fluoroskopi, dan tes thalium. Tanyakan ke dokter atau "
            "lihat laporan hasil pemeriksaan bila belum tahu."
        )
        values["restecg"] = _choice("Hasil EKG saat istirahat", RESTECG_OPTIONS)
        values["thalach"] = st.number_input(
            "Detak jantung maksimum saat uji treadmill (kali/menit)",
            min_value=60, max_value=220, value=None, step=1, placeholder="Contoh: 150",
        )
        values["oldpeak"] = st.number_input(
            "Penurunan segmen ST saat latihan (oldpeak)",
            min_value=0.0, max_value=6.5, value=None, step=0.1, placeholder="Contoh: 1.0",
        )
        values["slope"] = _choice("Kemiringan segmen ST saat latihan", SLOPE_OPTIONS)
        values["ca"] = _choice(
            "Jumlah pembuluh darah utama yang tampak pada fluoroskopi", CA_OPTIONS,
        )
        values["thal"] = _choice("Hasil tes thalium", THAL_OPTIONS)

        submitted = st.form_submit_button("Cek Risiko", type="primary")

    if not submitted:
        return None

    missing = [FIELD_LABELS[key] for key in FIELD_LABELS if values.get(key) is None]
    if missing:
        st.error("Lengkapi dulu semua isian. Belum diisi: " + ", ".join(missing) + ".")
        return None

    features = {key: float(values[key]) for key in FIELD_LABELS}
    return features, []
