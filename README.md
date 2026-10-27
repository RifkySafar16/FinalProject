# FinalProject

Aplikasi edukasi kesehatan dengan API FastAPI untuk tanya jawab berbasis
panduan PDF (RAG) dan prediksi penyakit jantung menggunakan model machine
learning.

> Hasil aplikasi ini hanya untuk edukasi dan bukan pengganti saran tenaga
> kesehatan atau diagnosis medis.

## Struktur Proyek

```text
.
├── data/
│   └── processed/           # Dataset yang telah dibersihkan
├── docs/                    # Dokumentasi
├── src/
│   ├── backend/             # FastAPI app, schemas, dan route
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── routes/
│   │       ├── chat.py
│   │       └── predict.py
│   ├── ml/                  # Preprocessing, training, dan prediksi
│   └── rag/                 # Ingest dokumen, prompt, dan RAG engine
├── tests/
└── requirements.txt
```

## Persyaratan

- Python 3.12 atau lebih baru
- API key Groq untuk endpoint chat
- File PDF panduan kesehatan untuk membuat indeks RAG

## Instalasi

Dari root repository, buat dan aktifkan virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Di Windows PowerShell, aktifkan environment dengan:

```powershell
.venv\Scripts\Activate.ps1
```

## Konfigurasi

Buat file `.env` di root repository:

```dotenv
GROQ_API_KEY=your-groq-api-key
PDF_PATH=/path/to/health-guide.pdf
```

`PDF_PATH` juga dapat berupa path relatif terhadap root repository, misalnya
`data/health-guide.pdf`. Jangan commit `.env` atau membagikan API key.

## Membuat indeks dokumen RAG

Jalankan proses ingest dari root repository setelah mengatur `PDF_PATH`:

```bash
python src/rag/ingest.py
```

Proses ini membuat `vectorstore/docs.pkl`. Buat ulang indeks jika PDF berubah
atau file indeks terhapus. Ingest melewati 14 halaman pertama dan 15 halaman
terakhir, serta halaman referensi atau halaman dengan kurang dari 300 karakter.

## Menjalankan API

Setelah dependensi, `.env`, dan indeks dokumen tersedia:

```bash
uvicorn src.backend.main:app --reload
```

- Dokumentasi Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI JSON: <http://127.0.0.1:8000/openapi.json>

Server mengaktifkan CORS untuk `http://localhost:3000` dan
`http://127.0.0.1:5173`. Sesuaikan daftar origin di `src/backend/main.py`
jika frontend menggunakan alamat lain.

## API

### `POST /chat`

Meminta jawaban berdasarkan panduan PDF. `question` harus berisi 3–500
karakter. Respons memuat jawaban bahasa Indonesia dengan disclaimer medis
dan daftar sumber halaman PDF.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Apa isi panduan tentang kesehatan jantung?"}'
```

Contoh respons:

```json
{
  "answer": "Jawaban berdasarkan panduan. ⚠️ Ini bukan nasihat medis.",
  "sources": [
    {
      "page": 84,
      "snippet": "Potongan teks sumber dari panduan..."
    }
  ]
}
```

### `POST /predict`

Menghasilkan skor heuristik berbasis aturan dengan kategori `low`, `moderate`,
atau `high`. Request memerlukan 13 fitur numerik:
`age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`,
`oldpeak`, `slope`, `ca`, dan `thal`.

Contoh request:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "age": 70, "sex": 1, "cp": 1, "trestbps": 180, "chol": 400,
    "fbs": 1, "restecg": 1, "thalach": 90, "exang": 1, "oldpeak": 2,
    "slope": 3, "ca": 3, "thal": 7
  }'
```

Respons mencakup `risk_level`, `score`, `max_score`, serta `factors` berisi
kontribusi setiap fitur yang menambah skor. Nilai sistolik `trestbps` di luar
rentang input yang diterima (70–250 mmHg), termasuk 400 mmHg, ditolak dengan
HTTP 422. Kategori fitur harus sesuai definisi dataset.

**Penting:** ini adalah heuristik edukasi berbobot yang dibuat agar aturannya
transparan dan dapat diuji; ini bukan kalkulator risiko klinis tervalidasi,
bukan diagnosis, dan bukan pengganti penilaian tenaga kesehatan. Batas usia, denyut jantung, serta ST depression adalah asumsi heuristik, bukan
cut-off diagnostik. Skor tidak boleh digunakan untuk keputusan medis.

Ambang tekanan darah sistolik mengacu secara umum pada kategori CDC: normal di
bawah 120, 120–129 elevated, dan tekanan darah tinggi mulai 130 mmHg. Ini
hanya mengatur poin faktor sistolik, bukan kategori diagnosis atau risiko
jantung klinis. Ambang kolesterol total menggunakan pedoman umum MedlinePlus
(<200 mg/dL diinginkan dan >=240 mg/dL tinggi).
Pemetaan kode kategori mengikuti deskripsi Cleveland Heart Disease dari UCI.
Bobot, pengelompokan skor, batas input sistolik 70–250, dan interpretasi
gabungan fitur adalah asumsi rekayasa yang belum divalidasi secara klinis.
Referensi: [CDC tentang tekanan darah](https://www.cdc.gov/high-blood-pressure/about/index.html),
[MedlinePlus tentang kolesterol](https://medlineplus.gov/cholesterollevelswhatyouneedtoknow.html),
dan [UCI Cleveland Heart Disease dataset](https://archive.ics.uci.edu/dataset/45/heart+disease).
Pelatihan model machine learning lama tetap tersedia melalui
`python -m src.ml.train`, tetapi tidak digunakan oleh endpoint `/predict`.

## Menjalankan Tes

Jalankan tes API dan RAG:

```bash
python -m pytest -q tests/test_main.py tests/test_backend_routes.py \
  tests/test_risk.py tests/test_rag.py
```

Tes modul machine learning lama di `tests/test_ml.py` memerlukan file
`models/heart_model.pkl`; endpoint `/predict` dan tes aturan risikonya tidak
memerlukan artifact tersebut.

## Dokumentasi Tambahan

- [Panduan penggunaan RAG](docs/rag_engine_usage.md)
