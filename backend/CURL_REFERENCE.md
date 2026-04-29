# Review Intelligence API — cURL Reference

Base URL: `http://localhost:8000`

---

## 1. GET /health

```bash
curl -X GET http://localhost:8000/health
```

**Response 200**
```json
{
  "status": "ok",
  "timestamp": "2025-04-25T10:30:00Z",
  "service": "Review Intelligence API",
  "version": "1.0.0"
}
```

---

## 2. POST /analyze — Single Review

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The food was absolutely delicious but delivery took over an hour. Very disappointing wait time."
  }'
```

**Response 200**
```json
{
  "id": "3f8a1c2d-4b5e-6789-abcd-ef0123456789",
  "created_at": "2025-04-25T10:31:00Z",
  "text": "The food was absolutely delicious but delivery took over an hour. Very disappointing wait time.",
  "sentiment": "mixed",
  "confidence": 0.83,
  "aspects": [
    { "aspect": "food", "sentiment": "positive", "score": 0.95 },
    { "aspect": "delivery", "sentiment": "negative", "score": 0.88 },
    { "aspect": "wait time", "sentiment": "negative", "score": 0.85 }
  ],
  "summary": "Customer was pleased with food quality but very dissatisfied with the long delivery time.",
  "suggested_reply": "Thank you for your kind words about our food! We sincerely apologise for the extended delivery time and are actively working to improve our logistics. We hope to serve you better next time.",
  "key_phrases": ["absolutely delicious", "over an hour", "very disappointing", "wait time"]
}
```

**Error responses**

| Status | Meaning |
|--------|---------|
| 400 | Validation error (text too short/long) |
| 503 | Groq API key missing or service unavailable |
| 500 | Internal analysis failure |

---

## 3. POST /bulk-analyze — Multiple Reviews

```bash
curl -X POST http://localhost:8000/bulk-analyze \
  -H "Content-Type: application/json" \
  -d '{
    "reviews": [
      "Great support team, resolved my issue in minutes!",
      "Price is way too high for what you get.",
      "Delivery was late and packaging was damaged.",
      "Excellent product quality, will buy again.",
      "The mobile app keeps crashing. Very frustrating."
    ]
  }'
```

**Response 200**
```json
{
  "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total": 5,
  "status": "completed",
  "created_at": "2025-04-25T10:32:00Z",
  "completed_at": "2025-04-25T10:32:08Z",
  "results": [
    {
      "text": "Great support team, resolved my issue in minutes!",
      "sentiment": "positive",
      "confidence": 0.96,
      "aspects": [
        { "aspect": "support", "sentiment": "positive", "score": 0.97 },
        { "aspect": "resolution time", "sentiment": "positive", "score": 0.94 }
      ],
      "summary": "Customer highly praised the support team for fast issue resolution.",
      "suggested_reply": "Thank you so much for the kind feedback! We're thrilled our support team could resolve your issue quickly.",
      "key_phrases": ["great support team", "resolved in minutes"],
      "error": null
    },
    {
      "text": "Price is way too high for what you get.",
      "sentiment": "negative",
      "confidence": 0.88,
      "aspects": [
        { "aspect": "price", "sentiment": "negative", "score": 0.91 },
        { "aspect": "value", "sentiment": "negative", "score": 0.84 }
      ],
      "summary": "Customer feels the product is overpriced and does not offer good value.",
      "suggested_reply": "We appreciate your honest feedback. We're constantly reviewing our pricing to ensure it reflects the value we provide. We'd love to hear more about what would make it worthwhile for you.",
      "key_phrases": ["too high", "not worth it"],
      "error": null
    },
    {
      "text": "Delivery was late and packaging was damaged.",
      "sentiment": "negative",
      "confidence": 0.91,
      "aspects": [
        { "aspect": "delivery", "sentiment": "negative", "score": 0.93 },
        { "aspect": "packaging", "sentiment": "negative", "score": 0.89 }
      ],
      "summary": "Customer experienced late delivery and received a damaged package.",
      "suggested_reply": "We sincerely apologise for the late delivery and the damaged packaging. Please contact our support team so we can make this right for you immediately.",
      "key_phrases": ["late delivery", "damaged packaging"],
      "error": null
    },
    {
      "text": "Excellent product quality, will buy again.",
      "sentiment": "positive",
      "confidence": 0.94,
      "aspects": [
        { "aspect": "product quality", "sentiment": "positive", "score": 0.96 }
      ],
      "summary": "Customer is very satisfied with product quality and intends to repurchase.",
      "suggested_reply": "Thank you for the wonderful review! We're delighted you love our product and look forward to serving you again.",
      "key_phrases": ["excellent quality", "will buy again"],
      "error": null
    },
    {
      "text": "The mobile app keeps crashing. Very frustrating.",
      "sentiment": "negative",
      "confidence": 0.89,
      "aspects": [
        { "aspect": "app stability", "sentiment": "negative", "score": 0.92 },
        { "aspect": "mobile app", "sentiment": "negative", "score": 0.90 }
      ],
      "summary": "Customer is frustrated by repeated mobile app crashes.",
      "suggested_reply": "We apologise for the poor app experience. Our development team is aware of stability issues and is working on a fix. Please update to the latest version or reach out to support for immediate assistance.",
      "key_phrases": ["keeps crashing", "very frustrating", "mobile app"],
      "error": null
    }
  ]
}
```

> 💡 **Save the `batch_id`** — use it with `/summary/{batch_id}` for aggregate insights.

---

## 4. GET /summary/{batch_id}

```bash
curl -X GET http://localhost:8000/summary/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response 200**
```json
{
  "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_reviews": 5,
  "created_at": "2025-04-25T10:32:00Z",
  "sentiment_distribution": {
    "positive": 2,
    "negative": 3,
    "neutral": 0,
    "mixed": 0
  },
  "sentiment_percentages": {
    "positive": 40.0,
    "negative": 60.0,
    "neutral": 0.0,
    "mixed": 0.0
  },
  "frequent_aspects": [
    { "aspect": "delivery",       "count": 2, "positive_count": 0, "negative_count": 2 },
    { "aspect": "support",        "count": 1, "positive_count": 1, "negative_count": 0 },
    { "aspect": "price",          "count": 1, "positive_count": 0, "negative_count": 1 },
    { "aspect": "product quality","count": 1, "positive_count": 1, "negative_count": 0 },
    { "aspect": "mobile app",     "count": 1, "positive_count": 0, "negative_count": 1 }
  ],
  "top_complaints": [
    "Delivery is frequently late and packages arrive damaged",
    "Pricing is considered too high relative to perceived value",
    "The mobile app has persistent crashing and stability issues"
  ],
  "top_praise": [
    "Support team is fast, responsive, and effective at resolving issues",
    "Product quality is consistently rated excellent by satisfied customers"
  ],
  "executive_summary": "Of the 5 reviews analysed, 60% are negative, highlighting systemic issues with delivery reliability, app stability, and pricing perception. Positive sentiment is concentrated around support team performance and product quality. Priority actions should focus on logistics improvements, mobile app stability fixes, and a pricing communication strategy to better convey value to customers."
}
```

**Error responses**

| Status | Meaning |
|--------|---------|
| 404 | batch_id not found |
| 202 | Batch is still processing |

---

## 5. GET /history

### Default (first page)
```bash
curl -X GET "http://localhost:8000/history"
```

### With pagination
```bash
curl -X GET "http://localhost:8000/history?page=2&limit=10"
```

### With date range filter
```bash
curl -X GET "http://localhost:8000/history?date_from=2025-04-01&date_to=2025-04-30&limit=50"
```

**Response 200**
```json
{
  "total": 6,
  "page": 1,
  "limit": 20,
  "pages": 1,
  "records": [
    {
      "id": "9d8e7f6a-5b4c-3d2e-1f0a-b1c2d3e4f5a6",
      "type": "single",
      "created_at": "2025-04-25T10:31:00Z",
      "text": "The food was absolutely delicious but delivery took over an hour.",
      "sentiment": "mixed",
      "confidence": 0.83,
      "summary": "Customer was pleased with food quality but dissatisfied with delivery time."
    },
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-012345678901",
      "type": "bulk",
      "batch_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "review_index": 0,
      "created_at": "2025-04-25T10:32:01Z",
      "text": "Great support team, resolved my issue in minutes!",
      "sentiment": "positive",
      "confidence": 0.96,
      "summary": "Customer highly praised the support team for fast issue resolution."
    }
  ]
}
```

---

## 6. POST /upload-csv — CSV File Upload

### Prepare a CSV file

`reviews.csv`:
```
text
"The product quality exceeded my expectations. Very happy with my purchase."
"Customer service was rude and unhelpful. Will not return."
"Fast shipping and great packaging. Exactly as described."
"The app UI is confusing and hard to navigate."
"Affordable price and decent quality for the money."
```

### Upload
```bash
curl -X POST http://localhost:8000/upload-csv \
  -F "file=@reviews.csv"
```

**Response 200** — Same structure as `/bulk-analyze`, plus batch_id for summary.
```json
{
  "batch_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
  "total": 5,
  "status": "completed",
  "created_at": "2025-04-25T10:35:00Z",
  "completed_at": "2025-04-25T10:35:09Z",
  "results": [ "..." ]
}
```

**Accepted CSV column names** (case-insensitive):
`review` | `text` | `comment` | `feedback` | `description` | `content`

If none of these are found, the **first column** is used as the review text.

**Error responses**

| Status | Meaning |
|--------|---------|
| 400 | Not a .csv file, or exceeds 500-row limit |
| 422 | CSV parsed but no review text found |

---

## Error Response Shape

All errors follow this shape:

```json
{
  "detail": "Human-readable error message here"
}
```

---

## Quick-start test sequence

```bash
# 1. Confirm the server is up
curl http://localhost:8000/health

# 2. Analyse one review
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Fantastic product but the price feels steep."}'

# 3. Bulk analyse and capture the batch_id
BATCH_ID=$(curl -s -X POST http://localhost:8000/bulk-analyze \
  -H "Content-Type: application/json" \
  -d '{"reviews": ["Love it!", "Terrible experience.", "Okay but pricey."]}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['batch_id'])")

# 4. Get aggregate summary for that batch
curl http://localhost:8000/summary/$BATCH_ID

# 5. View history
curl "http://localhost:8000/history?limit=5"

# 6. Upload a CSV
curl -X POST http://localhost:8000/upload-csv -F "file=@reviews.csv"
```
