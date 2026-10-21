# RAG backend usage

## Configure the environment

Install the project dependencies and set these values in the repository-root
`.env` file:

```dotenv
PDF_PATH=data/your-guide.pdf
GROQ_API_KEY=your-groq-api-key
```

`PDF_PATH` may be an absolute path or a path relative to the repository root.
Do not commit `.env` or API keys.

## Build the document index

Generate `vectorstore/docs.pkl` once before starting the API, and again whenever
the PDF changes or the index is deleted:

```bash
python3 src/rag/ingest.py
```

Ingest skips the first 14 and last 15 PDF pages, reference pages, and pages
with fewer than 300 characters. The generated index is stored at the
repository root, regardless of the current working directory.

## Call `ask()`

`ask(question)` returns a dictionary with an Indonesian `answer` ending in
`⚠️ Ini bukan nasihat medis.` and a `sources` list. Source page numbers are
1-based PDF page numbers; each snippet contains up to 200 characters.

Run the API from the repository root after building the index:

```bash
uvicorn src.backend.main:app --reload
```

Send a request with:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Apa isi panduan tentang kesehatan jantung?"}'
```

The endpoint is implemented in `src/backend/routes/chat.py` and registered by
`src/backend/main.py`. A blank
`question` must contain 3-500 characters or it is rejected with HTTP 422.
Cross-origin requests are enabled for `http://localhost:3000` and
`http://127.0.0.1:5173`; update `allow_origins` in `src/backend/main.py` if the
frontend runs from a different origin.

The `/predict` endpoint is implemented in `src/backend/routes/predict.py`. It
expects the 13 heart-disease features defined in `src/backend/schemas.py`. Before
using it, generate `models/heart_model.pkl` by running the training pipeline:

```bash
python -m src.ml.train
```

Until that model file exists, `/predict` returns HTTP 503.

The response shape is:

```json
{
  "answer": "Jawaban dalam bahasa Indonesia. ⚠️ Ini bukan nasihat medis.",
  "sources": [
    {
      "page": 84,
      "snippet": "Relevant text from the PDF..."
    }
  ]
}
```

The RAG module raises a clear error if the index or `GROQ_API_KEY` is missing,
or if the supplied question is empty.