#!/usr/bin/env bash
# Menyalakan backend FastAPI (hanya di dalam container, port 8000) dan
# frontend Streamlit di port $PORT (diberikan Render; default 10000).
set -e
cd "$(dirname "$0")/.."

PORT="${PORT:-10000}"

if [ -z "$GROQ_API_KEY" ]; then
  echo "PERINGATAN: GROQ_API_KEY belum diisi. Fitur chat tidak akan berjalan."
fi

echo "Menyalakan backend FastAPI di 127.0.0.1:8000 ..."
python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 &

# Frontend langsung dinyalakan supaya port publik cepat terbuka.
# Selama backend masih memuat, sidebar menampilkan "Server tidak terhubung".
export API_URL=http://127.0.0.1:8000
echo "Menyalakan frontend Streamlit di port ${PORT} ..."
exec python -m streamlit run src/frontend/app.py \
  --server.port "${PORT}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false \
  --client.toolbarMode minimal
