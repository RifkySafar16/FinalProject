# Deploy — Heart Risk Advisor

Aplikasi online di-deploy ke **Streamlit Community Cloud** (gratis, tanpa kartu).
Folder ini juga berisi konfigurasi **Docker** (dipakai untuk menjalankan aplikasi
lengkap di komputer/server mana pun, dan siap dipakai di Render bila tim punya akun
dengan kartu terverifikasi).

## Isi folder

| File | Fungsi |
|---|---|
| `streamlit_cloud/streamlit_app.py` | Peluncur untuk Streamlit Cloud: siapkan model + indeks RAG, nyalakan backend FastAPI, lalu tampilkan frontend |
| `streamlit_cloud/requirements.txt` | Paket untuk Streamlit Cloud (dibaca lebih dulu daripada `requirements.txt` di root, sehingga torch tidak ikut terpasang) |
| `../Dockerfile`, `../.dockerignore` | Image Docker: pasang paket, latih model, buat indeks RAG |
| `start.sh` | Perintah start di dalam container: backend (port 8000, internal) + frontend (port `$PORT`, default 10000) |
| `requirements-deploy.txt` | Paket yang sudah diuji untuk Docker (isi sama dengan `streamlit_cloud/requirements.txt`) |
| `who_cvd_guideline_2007.pdf` | Pedoman WHO 2007 untuk RAG (`data/raw/` di-ignore, jadi disimpan di sini) |

## Streamlit Community Cloud

Streamlit Cloud hanya bisa deploy dari repo milik sendiri, jadi aplikasi dijalankan
dari **fork** repo ini (semua branch ikut di-fork).

| Isian | Nilai |
|---|---|
| Repository | `<akun-github>/FinalProject` (fork) |
| Branch | `Yu` |
| Main file path | `deploy/streamlit_cloud/streamlit_app.py` |
| Python version (Advanced settings) | 3.12 |
| Secrets (Advanced settings) | `GROQ_API_KEY = "gsk_..."` |

- Pengunjung pertama setelah server menyala menunggu ±1–3 menit (latih model + buat indeks).
  Pengunjung berikutnya langsung masuk.
- Aplikasi tidur setelah 12 jam tanpa pengunjung; buka URL beberapa menit sebelum demo.
- Untuk memperbarui aplikasi setelah ada perubahan di repo tim: buka fork di GitHub →
  **Sync fork**, lalu di Streamlit Cloud pilih **Reboot app**.

## Docker (komputer sendiri / server)

```bash
docker build -t heart-risk-advisor .
docker run -p 10000:10000 -e GROQ_API_KEY=xxx heart-risk-advisor
```

Lalu buka http://localhost:10000.

Pemakaian RAM terukur ±280 MB (backend ±190 MB, frontend ±95 MB).
