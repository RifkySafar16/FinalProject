"""Form data kesehatan untuk endpoint /predict.

Model membutuhkan 13 fitur. Tujuh data dasar wajib diisi pengguna.
Enam data klinis bersifat opsional: bila tidak diisi, dipakai nilai
bawaan (median/modus data latih Cleveland) dan hasil ditandai kurang akurat.
"""

from __future__ import annotations

import streamlit as st

# Nilai bawaan data klinis = median (angka) atau modus (kategori)
# dari data/processed/cleveland_clean.csv.
CLINICAL_DEFAULTS: dict[str, float] = {
    "restecg": 0,
    "thalach": 153,
    "oldpeak": 0.8,
    "slope": 1,
    "ca": 0,
    "thal": 3,
}

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
THAL_OPTIONS = {
    3: "Normal",
    6: "Kelainan menetap (fixed defect)",
    7: "Kelainan yang dapat pulih (reversible defect)",
}


def render_form() -> tuple[dict[str, float], list[str]] | None:
    """Tampilkan form. Kembalikan (fitur, daftar_data_diperkirakan) saat dikirim."""
    with st.form("form_risiko"):
        st.subheader("Data dasar")

        age = st.number_input(
            "Usia (tahun)", min_value=18, max_value=100, value=50, step=1,
            help="Data acuan (dataset Cleveland) berisi pasien berusia 29–77 tahun.",
        )
        sex = st.radio(
            "Jenis kelamin", ["Laki-laki", "Perempuan"], horizontal=True,
        )
        trestbps = st.number_input(
            "Tekanan darah atas / sistolik (mmHg)",
            min_value=80, max_value=220, value=120, step=1,
            help="Angka pertama hasil tensi. Contoh: tensi 120/80 → isi 120.",
        )
        chol = st.number_input(
            "Kolesterol total (mg/dl)",
            min_value=100, max_value=600, value=200, step=1,
            help="Bila hasil lab dalam mmol/l, kalikan 38,67. Contoh: 5,2 mmol/l ≈ 201 mg/dl.",
        )
        fbs_answer = st.radio(
            "Gula darah puasa di atas 120 mg/dl?",
            ["Tidak", "Ya", "Tidak tahu"], horizontal=True,
        )
        cp = st.selectbox(
            "Keluhan nyeri dada",
            options=list(CHEST_PAIN_OPTIONS),
            format_func=CHEST_PAIN_OPTIONS.get,
            help=CHEST_PAIN_HELP,
        )
        exang_answer = st.radio(
            "Nyeri dada saat olahraga atau aktivitas berat?",
            ["Tidak", "Ya"], horizontal=True,
        )

        with st.expander("Data klinis dari hasil pemeriksaan (opsional)"):
            use_clinical = st.checkbox(
                "Pakai data klinis yang saya isi di bawah",
                help="Biarkan kosong bila tidak punya hasil EKG, uji treadmill, "
                     "atau pemeriksaan jantung lain. Sistem akan memakai nilai rata-rata.",
            )
            restecg = st.selectbox(
                "Hasil EKG saat istirahat", list(RESTECG_OPTIONS),
                format_func=RESTECG_OPTIONS.get,
            )
            thalach = st.number_input(
                "Detak jantung maksimum saat uji treadmill (kali/menit)",
                min_value=60, max_value=220, value=int(CLINICAL_DEFAULTS["thalach"]),
            )
            oldpeak = st.number_input(
                "Penurunan segmen ST saat latihan (oldpeak)",
                min_value=0.0, max_value=6.5, value=CLINICAL_DEFAULTS["oldpeak"], step=0.1,
            )
            slope = st.selectbox(
                "Kemiringan segmen ST saat latihan", list(SLOPE_OPTIONS),
                format_func=SLOPE_OPTIONS.get,
            )
            ca = st.selectbox(
                "Jumlah pembuluh darah utama yang tampak pada fluoroskopi",
                [0, 1, 2, 3],
            )
            thal = st.selectbox(
                "Hasil tes thalium", list(THAL_OPTIONS),
                format_func=THAL_OPTIONS.get,
            )

        submitted = st.form_submit_button("Cek Risiko", type="primary")

    if not submitted:
        return None

    estimated: list[str] = []
    fbs = 1 if fbs_answer == "Ya" else 0
    if fbs_answer == "Tidak tahu":
        estimated.append("gula darah puasa (dianggap normal)")

    features: dict[str, float] = {
        "age": float(age),
        "sex": 1.0 if sex == "Laki-laki" else 0.0,
        "cp": float(cp),
        "trestbps": float(trestbps),
        "chol": float(chol),
        "fbs": float(fbs),
        "exang": 1.0 if exang_answer == "Ya" else 0.0,
    }

    if use_clinical:
        features.update({
            "restecg": float(restecg),
            "thalach": float(thalach),
            "oldpeak": float(oldpeak),
            "slope": float(slope),
            "ca": float(ca),
            "thal": float(thal),
        })
    else:
        features.update({k: float(v) for k, v in CLINICAL_DEFAULTS.items()})
        estimated.append("6 data klinis (memakai nilai rata-rata)")

    return features, estimated
