# Dokumentasi API: Heart Disease Risk Advisor

Backend dibangun dengan FastAPI (`src/backend/`) dan menjadi satu-satunya pintu yang dipanggil frontend. Saat dijalankan lokal, alamat dasarnya `http://127.0.0.1:8000`. Dokumentasi interaktif otomatis (Swagger UI) tersedia di `http://127.0.0.1:8000/docs`, tempat endpoint bisa dicoba langsung dari browser.

> **Catatan verifikasi untuk penyusun (hapus setelah diperiksa):** nama field di bawah mengikuti kolom dataset UCI dan Tabel 4.5 laporan. Cocokkan dengan Swagger UI (`/docs`) saat backend berjalan, dan perbaiki bila ada yang berbeda.

## Ringkasan endpoint

| Endpoint | Fungsi | Masukan | Keluaran |
|---|---|---|---|
| `POST /predict` | Skor risiko penyakit jantung | 13 fitur numerik | `risk_level`, `score`, `max_score`, `factors`, `disclaimer` |
| `POST /chat` | Tanya jawab pedoman WHO 2007 | `question` (3 sampai 500 karakter) | `answer`, `sources` |

## POST /predict

Menghitung skor risiko penyakit jantung dengan aturan sederhana dan transparan (`src/ml/risk.py`). Setiap faktor diberi poin; total poin menentukan kategori risiko. Semua 13 fitur wajib dikirim; frontend juga mewajibkan pengguna mengisi ke-13 data sebelum memanggil endpoint ini.

### Body (JSON)

| Field | Arti | Nilai yang valid |
|---|---|---|
| `age` | Usia (tahun) | angka |
| `sex` | Jenis kelamin | 1 = laki-laki, 0 = perempuan |
| `cp` | Jenis nyeri dada | 1 sampai 4 |
| `trestbps` | Tekanan darah sistolik saat istirahat (mmHg) | angka |
| `chol` | Kolesterol total (mg/dl) | angka |
| `fbs` | Gula darah puasa > 120 mg/dl | 1 = ya, 0 = tidak |
| `restecg` | Hasil EKG saat istirahat | 0 sampai 2 |
| `thalach` | Detak jantung maksimum saat uji latihan | angka |
| `exang` | Nyeri dada saat olahraga | 1 = ya, 0 = tidak |
| `oldpeak` | Penurunan segmen ST saat latihan | angka |
| `slope` | Kemiringan segmen ST | 1 sampai 3 |
| `ca` | Jumlah pembuluh utama pada fluoroskopi | 0 sampai 3 |
| `thal` | Hasil tes thalium | 3, 6, atau 7 |

Jenis dan rentang divalidasi oleh Pydantic.

### Contoh permintaan (profil B pada laporan)

```json
{
  "age": 58, "sex": 1, "cp": 4, "trestbps": 150, "chol": 260,
  "fbs": 0, "restecg": 0, "thalach": 153, "exang": 1,
  "oldpeak": 0.8, "slope": 1, "ca": 0, "thal": 3
}
```

### Contoh respons (200)

```json
{
  "risk_level": "moderate",
  "score": 19,
  "max_score": 41,
  "factors": [
    {"feature": "age", "value": 58.0, "points": 2, "reason": "usia 45-64 tahun (ambang heuristik)"},
    {"feature": "trestbps", "value": 150.0, "points": 6, "reason": "tekanan sistolik istirahat >=130 mmHg"},
    {"feature": "exang", "value": 1.0, "points": 4, "reason": "ada angina saat olahraga"}
  ],
  "disclaimer": "Skor ini adalah heuristik edukasi, bukan diagnosis atau kalkulator risiko klinis tervalidasi. Konsultasikan hasil kesehatan dengan tenaga medis."
}
```

Daftar `factors` di atas dipersingkat; respons asli profil B memuat 7 faktor. Kategori: `low` skor 0–10, `moderate` 11–22, `high` 23 ke atas.

### Kode respons

| Kode | Arti |
|---|---|
| 200 | Berhasil |
| 422 | Input tidak valid (tipe atau rentang salah, field hilang) |

### Catatan
- Respons `/predict` membawa `disclaimer` sendiri; frontend menampilkannya di bawah hasil.
- Kategori risiko ditentukan oleh API (`risk_level`), lalu frontend menerjemahkannya menjadi rendah, sedang, atau tinggi.

## POST /chat

Menjawab pertanyaan pencegahan penyakit jantung dalam bahasa Indonesia, bersumber dari pedoman WHO 2007.

### Body (JSON)

| Field | Tipe | Aturan |
|---|---|---|
| `question` | string | 3 sampai 500 karakter |

```json
{ "question": "Berapa batas konsumsi garam per hari?" }
```

### Contoh respons (200)

```json
{
  "answer": "... ⚠️ Ini bukan nasihat medis.",
  "sources": [
    { "page": 29, "snippet": "(200 karakter pertama potongan teks sumber)" }
  ]
}
```

| Field | Arti |
|---|---|
| `answer` | Jawaban bahasa Indonesia. Selalu diakhiri disclaimer (ditambahkan oleh kode) |
| `sources` | Daftar sumber: `page` = nomor halaman **PDF** (halaman cetak pedoman berselisih 6), `snippet` = 200 karakter pertama potongan teks |

Bila informasi tidak ada di pedoman, jawabannya "Maaf, informasi tidak ditemukan." Catatan: sumber tetap dikembalikan pada kasus itu (temuan laporan Bab 5.5 no.3).

### Kode respons

| Kode | Arti |
|---|---|
| 200 | Berhasil |
| 422 | Pertanyaan terlalu pendek (< 3) atau terlalu panjang (> 500 karakter) |

### Perilaku yang perlu diketahui
- Waktu respons sekitar 1 sampai 3 detik, karena memanggil LLM di Groq (butuh internet dan `GROQ_API_KEY`).
- Saat LLM mengembalikan jawaban kosong, fungsi `ask()` melempar error (Issue #3). Endpoint `/chat` pada kasus ini mengembalikan **500 Internal Server Error** (terverifikasi 23 Oktober 2026).
- Chat belum mengingat pertanyaan sebelumnya. Setiap permintaan berdiri sendiri.

## Contoh pemakaian dari Python

```python
import requests

BASE = "http://127.0.0.1:8000"

risiko = requests.post(f"{BASE}/predict", json={
    "age": 58, "sex": 1, "cp": 4, "trestbps": 150, "chol": 260,
    "fbs": 0, "restecg": 0, "thalach": 153, "exang": 1,
    "oldpeak": 0.8, "slope": 1, "ca": 0, "thal": 3,
})
print(risiko.status_code, risiko.json())

jawaban = requests.post(f"{BASE}/chat", json={"question": "Apa saja faktor risiko penyakit jantung?"})
print(jawaban.status_code, jawaban.json())
```

## Pengujian terkait

- `tests/test_main.py` dan `tests/test_backend_routes.py`: aplikasi dan endpoint.
- `tests/test_injection.py`: uji serangan prompt injection pada modul RAG.
