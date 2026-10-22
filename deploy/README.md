# Deploy — Heart Risk Advisor

Aplikasi di-deploy ke **Render** (Web Service, Docker, paket gratis).

## Isi folder

| File | Fungsi |
|---|---|
| `../Dockerfile` | Resep image: pasang paket, latih model, buat indeks RAG |
| `../.dockerignore` | File yang tidak ikut ke image (venv, model lokal, `.env`) |
| `start.sh` | Menyalakan backend FastAPI (internal, port 8000) + frontend Streamlit (port `$PORT`) |
| `requirements-deploy.txt` | Paket Python yang sudah diuji (tanpa torch) |
| `who_cvd_guideline_2007.pdf` | Pedoman WHO 2007 untuk RAG (`data/raw/` di-ignore, jadi disimpan di sini) |

## Pengaturan Render

| Isian | Nilai |
|---|---|
| Source | Public Git Repository: `https://github.com/RifkySafar16/FinalProject` |
| Branch | `Yu` |
| Language / Runtime | Docker |
| Dockerfile Path | `./Dockerfile` |
| Instance Type | Free |
| Environment Variable | `GROQ_API_KEY` = kunci dari console.groq.com |

Setelah push ke branch `Yu`, buka Render → **Manual Deploy → Deploy latest commit**.

## Catatan paket gratis

- RAM 512 MB. Pemakaian terukur ±280 MB (backend ±190 MB, frontend ±95 MB).
- Aplikasi tidur setelah 15 menit tanpa pengunjung; akses berikutnya butuh ±1 menit.
  Buka URL beberapa menit sebelum demo.

## Menjalankan dengan Docker di komputer sendiri

```bash
docker build -t heart-risk-advisor .
docker run -p 10000:10000 -e GROQ_API_KEY=xxx heart-risk-advisor
```

Lalu buka http://localhost:10000.
