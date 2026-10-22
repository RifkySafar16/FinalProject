# Heart Risk Advisor — image Docker (dipakai Render, juga bisa dijalankan lokal)
#
# Build & jalankan lokal (bila Docker tersedia):
#   docker build -t heart-risk-advisor .
#   docker run -p 10000:10000 -e GROQ_API_KEY=xxx heart-risk-advisor
#   lalu buka http://localhost:10000
#
# Alur build:
#   1. Pasang paket Python (tanpa torch, supaya ringan)
#   2. Salin kode repo, salin PDF WHO ke data/raw/
#   3. Latih model dan buat indeks RAG
#   4. deploy/start.sh menyalakan backend FastAPI (internal) + frontend Streamlit (publik)
#
# Kunci GROQ_API_KEY TIDAK ditulis di sini; isi sebagai Environment Variable di Render.

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR $HOME/app

# 1. Paket Python (dipisah supaya cache build tidak hilang saat kode berubah)
COPY --chown=user deploy/requirements-deploy.txt deploy/requirements-deploy.txt
RUN pip install --no-cache-dir --user -r deploy/requirements-deploy.txt

# 2. Kode repo + PDF WHO
COPY --chown=user . .
RUN mkdir -p data/raw \
    && cp deploy/who_cvd_guideline_2007.pdf data/raw/who_cvd_guideline_2007.pdf

# 3. Model + indeks RAG
RUN python -m src.ml.train
RUN PDF_PATH=data/raw/who_cvd_guideline_2007.pdf python src/rag/ingest.py

# 4. Start
RUN sed -i 's/\r$//' deploy/start.sh
EXPOSE 10000
CMD ["bash", "deploy/start.sh"]
