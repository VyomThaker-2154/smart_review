from fastapi import APIRouter, HTTPException

from models import BulkReviewRequest, BulkReviewResponse, ReviewAnalysisResult
from llm_service import analyze_reviews_batch
from storage import store
from config import settings

router = APIRouter()


@router.post("/bulk-analyze", response_model=BulkReviewResponse)
async def bulk_analyze(request: BulkReviewRequest):
    """
    Analyse multiple reviews in one request.

    Each review is analysed individually.  Results include a batch_id that can
    be used with GET /summary/{batch_id} to retrieve aggregate insights.
    """
    if len(request.reviews) > settings.MAX_BULK_REVIEWS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many reviews. Maximum allowed per request: {settings.MAX_BULK_REVIEWS}",
        )

    batch_id = store.create_batch(source="api")

    try:
        raw_results = analyze_reviews_batch(request.reviews)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Bulk analysis failed: {str(exc)}")

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
