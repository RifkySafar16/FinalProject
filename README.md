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

Memprediksi klasifikasi penyakit jantung. Request memerlukan 13 fitur numerik:
`age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`,
`oldpeak`, `slope`, `ca`, dan `thal`.

Endpoint memerlukan file model `models/heart_model.pkl`. Buat model terlebih
dahulu (proses training dapat memerlukan waktu):

```bash
python -m src.ml.train
```

Jika model belum tersedia, endpoint mengembalikan HTTP 503. Gunakan
`/docs` untuk melihat schema request lengkap dan mencoba kedua endpoint.

## Menjalankan Tes

Jalankan tes API dan RAG:

```bash
python -m pytest -q tests/test_main.py tests/test_backend_routes.py tests/test_rag.py
```

Tes prediksi model yang sesungguhnya memerlukan file
`models/heart_model.pkl`.

## Dokumentasi Tambahan

- [Panduan penggunaan RAG](docs/rag_engine_usage.md)
