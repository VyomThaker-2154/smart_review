import io
import csv

from fastapi import APIRouter, UploadFile, File, HTTPException

from models import UploadCSVResponse, ReviewAnalysisResult, BulkReviewResponse
from llm_service import analyze_reviews_batch
from storage import store
from config import settings

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
    "application/octet-stream",
}


def _parse_csv(content: bytes) -> list[str]:
    """
    Extract review texts from a CSV file.

    Accepts:
    - Single-column CSV  (just the review text per row)
    - Multi-column CSV   (looks for a column named 'review', 'text',
                          'comment', 'feedback', or 'description')
    """
    text = content.decode("utf-8-sig").strip()
    reader = csv.DictReader(io.StringIO(text))

    # Try to find a text column by common names
    CANDIDATE_COLS = {"review", "text", "comment", "feedback", "description", "content"}

    rows = list(reader)
    if not rows:
        # Try as a plain single-column file
        lines = [l.strip().strip('"') for l in text.splitlines() if l.strip()]
        return [l for l in lines if l]

    fieldnames = [f.lower().strip() for f in (reader.fieldnames or [])]
    text_col = None
    for col in fieldnames:
        if col in CANDIDATE_COLS:
            text_col = col
            break

    if text_col is None and fieldnames:
        # Fall back to first column
        text_col = fieldnames[0]

    reviews = []
    original_fields = reader.fieldnames or []
    col_map = {f.lower().strip(): f for f in original_fields}
    actual_col = col_map.get(text_col, text_col)

    for row in rows:
        val = row.get(actual_col, "").strip()
        if val:
            reviews.append(val)

    return reviews


@router.post("/upload-csv", response_model=BulkReviewResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file of customer reviews for batch analysis.

    The CSV must contain a column named one of:
    review, text, comment, feedback, description, content
    — or the first column will be used as the review text.

    Returns the same payload as POST /bulk-analyze, including a batch_id
    for use with GET /summary/{batch_id}.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Only .csv files are accepted."
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        reviews = _parse_csv(content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse CSV: {exc}")

    if not reviews:
        raise HTTPException(
            status_code=422,
            detail="No review text found in the CSV. "
            "Ensure there is a column named review, text, comment, feedback, or description.",
        )

    if len(reviews) > settings.MAX_CSV_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"CSV contains {len(reviews)} rows; maximum allowed is {settings.MAX_CSV_ROWS}.",
        )

    batch_id = store.create_batch(source="csv")

    try:
        raw_results = analyze_reviews_batch(reviews)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    store.update_batch(batch_id, raw_results)
    batch = store.get_batch(batch_id)

    results = [
        ReviewAnalysisResult(
            text=r["text"],
            sentiment=r.get("sentiment", "neutral"),
            confidence=r.get("confidence", 0.0),
            aspects=r.get("aspects", []),
            summary=r.get("summary", ""),
            suggested_reply=r.get("suggested_reply", ""),
            key_phrases=r.get("key_phrases", []),
            error=r.get("error"),
        )
        for r in raw_results
    ]

    return BulkReviewResponse(
        batch_id=batch_id,
        total=len(results),
        status=batch["status"],
        results=results,
        created_at=batch["created_at"],
        completed_at=batch.get("completed_at"),
    )
