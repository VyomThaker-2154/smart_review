from collections import Counter
from fastapi import APIRouter, HTTPException

from models import SummaryResponse, SentimentDistribution, AspectFrequency
from llm_service import generate_batch_insights
from storage import store

router = APIRouter()


@router.get("/summary/{batch_id}", response_model=SummaryResponse)
async def get_summary(batch_id: str):
    """
    Generate aggregate insights for a completed batch.

    Computes sentiment distribution, frequent aspects, and calls the LLM once
    to produce top complaints, top praise, and an executive summary paragraph.
    """
    batch = store.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch '{batch_id}' not found.")

    if batch["status"] != "completed":
        raise HTTPException(
            status_code=202,
            detail=f"Batch is still '{batch['status']}'. Try again shortly.",
        )

    results = batch["results"]
    if not results:
        raise HTTPException(status_code=404, detail="Batch has no results.")

    # ── Sentiment distribution ─────────────────────────────────────────────
    dist = SentimentDistribution()
    for r in results:
        s = r.get("sentiment", "neutral")
        if s == "positive":
            dist.positive += 1
        elif s == "negative":
            dist.negative += 1
        elif s == "mixed":
            dist.mixed += 1
        else:
            dist.neutral += 1

    total = len(results)
    pct = {
        "positive": round(dist.positive / total * 100, 1),
        "negative": round(dist.negative / total * 100, 1),
        "neutral": round(dist.neutral / total * 100, 1),
        "mixed": round(dist.mixed / total * 100, 1),
    }

    # ── Aspect frequency ──────────────────────────────────────────────────
    aspect_counter: Counter = Counter()
    aspect_pos: Counter = Counter()
    aspect_neg: Counter = Counter()

    for r in results:
        for a in r.get("aspects", []):
            name = a.get("aspect", "").lower()
            if name:
                aspect_counter[name] += 1
                if a.get("sentiment") == "positive":
                    aspect_pos[name] += 1
                elif a.get("sentiment") == "negative":
                    aspect_neg[name] += 1

    frequent_aspects = [
        AspectFrequency(
            aspect=asp,
            count=cnt,
            positive_count=aspect_pos.get(asp, 0),
            negative_count=aspect_neg.get(asp, 0),
        )
        for asp, cnt in aspect_counter.most_common(10)
    ]

    # ── LLM insights ──────────────────────────────────────────────────────
    try:
        insights = generate_batch_insights(results)
    except Exception:
        insights = {
            "top_complaints": [],
            "top_praise": [],
            "executive_summary": f"Batch of {total} reviews analysed successfully.",
        }

    return SummaryResponse(
        batch_id=batch_id,
        total_reviews=total,
        sentiment_distribution=dist,
        sentiment_percentages=pct,
        top_complaints=insights.get("top_complaints", []),
        top_praise=insights.get("top_praise", []),
        frequent_aspects=frequent_aspects,
        executive_summary=insights.get("executive_summary", ""),
        created_at=batch["created_at"],
    )
