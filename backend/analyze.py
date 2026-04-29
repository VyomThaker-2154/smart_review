from fastapi import APIRouter, HTTPException

from models import SingleReviewRequest, SingleReviewResponse
from llm_service import analyze_single_review
from storage import store

router = APIRouter()


@router.post("/analyze", response_model=SingleReviewResponse)
async def analyze_review(request: SingleReviewRequest):
    """
    Analyse a single customer review.

    Returns sentiment, confidence, aspect-level breakdown, a concise summary,
    and a suggested business reply.
    """
    try:
        result = analyze_single_review(request.text)
    except RuntimeError as exc:
        # Missing API key or similar config error
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")

    # Persist to history
    record_id = store.add_to_history(
        {
            "type": "single",
            "text": request.text,
            "sentiment": result.get("sentiment"),
            "confidence": result.get("confidence"),
            "aspects": result.get("aspects", []),
            "summary": result.get("summary"),
            "suggested_reply": result.get("suggested_reply"),
            "key_phrases": result.get("key_phrases", []),
        }
    )

    # Fetch the stored record so created_at is populated
    history = store.get_history(page=1, limit=1)
    record = history["records"][0] if history["records"] else {}

    return SingleReviewResponse(
        id=record_id,
        created_at=record.get("created_at", ""),
        text=request.text,
        sentiment=result["sentiment"],
        confidence=result["confidence"],
        aspects=result["aspects"],
        summary=result["summary"],
        suggested_reply=result["suggested_reply"],
        key_phrases=result.get("key_phrases", []),
    )
