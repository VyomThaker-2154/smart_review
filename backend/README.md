# Review Intelligence API

AI-powered customer review analysis backend using FastAPI + Groq (LLaMA 3.3 70B).

## Project Structure

```
review-intelligence-api/
├── main.py              # FastAPI app, CORS, router registration
├── config.py            # Settings, env vars
├── models.py            # Pydantic request/response schemas
├── llm_service.py       # All Groq LLM calls (analyze, batch insights, reply gen)
├── storage.py           # In-memory store (history + batch state)
├── routers/
│   ├── health.py        # GET  /health
│   ├── analyze.py       # POST /analyze
│   ├── bulk_analyze.py  # POST /bulk-analyze
│   ├── summary.py       # GET  /summary/{batch_id}
│   ├── history.py       # GET  /history
│   └── upload_csv.py    # POST /upload-csv
├── requirements.txt
├── .env.example
└── CURL_REFERENCE.md    # All cURL commands + full response examples
```

## Setup

### 1. Get a Groq API key (free)
https://console.groq.com → Create an account → API Keys → Create key

### 2. Install dependencies
```bash
cd review-intelligence-api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY
```

### 4. Run the server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open interactive docs
http://localhost:8000/docs

---

## API Endpoints

| Method | Endpoint              | Purpose                              |
|--------|-----------------------|--------------------------------------|
| GET    | /health               | Service health check                 |
| POST   | /analyze              | Analyse a single review              |
| POST   | /bulk-analyze         | Analyse multiple reviews (JSON)      |
| GET    | /summary/{batch_id}   | Aggregate insights for a batch       |
| GET    | /history              | Paginated history of all analyses    |
| POST   | /upload-csv           | Upload CSV file for batch analysis   |

See `CURL_REFERENCE.md` for complete request/response examples.

---

## Frontend Integration Notes

The API is designed for two dashboard modes:

**Single review dashboard** → POST `/analyze`
- Returns: sentiment, confidence, aspects breakdown, summary, suggested reply, key_phrases
- Suitable for: sentiment gauge, aspect chips, reply composer

**Bulk/CSV dashboard** → POST `/bulk-analyze` or POST `/upload-csv`, then GET `/summary/{batch_id}`
- `/bulk-analyze` returns per-review results immediately
- `/summary/{batch_id}` returns: sentiment distribution pie, aspect frequency bar chart, top complaints/praise list, executive summary paragraph
- Suitable for: full analytics dashboard with charts and drill-down

---

## Models Used

- **Default:** `llama-3.3-70b-versatile` (Groq)
- Override via `GROQ_MODEL` in `.env`
- Compatible with any model on Groq's API

---

## Notes

- History is in-memory only — it resets on server restart (by design for a 1-week project)
- Bulk analysis processes reviews sequentially with a small delay to respect Groq's free-tier rate limits
- Max reviews per bulk request: 100; max CSV rows: 500 (configurable in `config.py`)
