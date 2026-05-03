"""
routers/scrape_analyze.py
─────────────────────────
POST /scrape-and-analyze

Single endpoint that:
  1. Scrapes Google Maps reviews for the given business
  2. Runs bulk LLM analysis on every scraped review
  3. Builds the summary (sentiment distribution, aspects, executive summary)
  4. Persists everything to the in-memory store
  5. Returns the full combined payload in one response

The response shape is deliberately a superset of BulkReviewResponse + SummaryResponse
so the frontend can render both the "bulk dashboard" and the summary panel from one call.
"""

import asyncio
from collections import Counter
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from scraper import scrape_sync
from llm_service import analyze_reviews_batch, generate_batch_insights
from storage import store
from models import (
    ReviewAnalysisResult,
    SentimentDistribution,
    AspectFrequency,
)

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class ScrapeAnalyzeRequest(BaseModel):
    business_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Name of the business / shop to look up on Google Maps",
        examples=["Cafe Coffee Day", "Domino's Pizza"],
    )
    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Optional city, area, or address to narrow the search",
        examples=["Bandra, Mumbai", "Connaught Place Delhi"],
    )
    max_reviews: int = Field(
        default=50,
        ge=5,
        le=200,
        description="Maximum number of reviews to scrape (5–200)",
    )
    sort_by_newest: bool = Field(
        default=False,
        description="If true, sort Google Maps reviews by newest before scraping",
    )


class ScrapedReviewMeta(BaseModel):
    author: str
    rating: Optional[float] = None
    date: str
    text: str


class ScrapeAnalyzeResponse(BaseModel):
    # ── Scrape metadata ──────────────────────────────────────────────────────
    business_name: str
    location: Optional[str]
    place_name: str                         # as shown on Google Maps
    place_url: str
    total_scraped: int
    scrape_error: Optional[str]             # non-fatal: partial results still returned

    # ── Batch / analysis ─────────────────────────────────────────────────────
    batch_id: str
    status: str
    created_at: str
    completed_at: Optional[str]

    # ── Per-review results ───────────────────────────────────────────────────
    reviews_raw: list[ScrapedReviewMeta]    # raw scraped data (author, rating, date, text)
    results: list[ReviewAnalysisResult]     # LLM analysis per review

    # ── Aggregate summary ────────────────────────────────────────────────────
    sentiment_distribution: SentimentDistribution
    sentiment_percentages: dict[str, float]
    frequent_aspects: list[AspectFrequency]
    top_complaints: list[str]
    top_praise: list[str]
    executive_summary: str
    average_rating: Optional[float]         # mean star rating from scraped data


# ── Helper ────────────────────────────────────────────────────────────────────

def _build_summary(results: list[dict]) -> dict:
    """Compute sentiment distribution + aspect frequency from analysis results."""
    dist = SentimentDistribution()
    aspect_counter: Counter = Counter()
    aspect_pos: Counter = Counter()
    aspect_neg: Counter = Counter()

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

        for a in r.get("aspects", []):
            name = a.get("aspect", "").lower()
            if name:
                aspect_counter[name] += 1
                if a.get("sentiment") == "positive":
                    aspect_pos[name] += 1
                elif a.get("sentiment") == "negative":
                    aspect_neg[name] += 1

    total = len(results) or 1
    pct = {
        "positive": round(dist.positive / total * 100, 1),
        "negative": round(dist.negative / total * 100, 1),
        "neutral":  round(dist.neutral  / total * 100, 1),
        "mixed":    round(dist.mixed    / total * 100, 1),
    }

    frequent_aspects = [
        AspectFrequency(
            aspect=asp,
            count=cnt,
            positive_count=aspect_pos.get(asp, 0),
            negative_count=aspect_neg.get(asp, 0),
        )
        for asp, cnt in aspect_counter.most_common(10)
    ]

    return {
        "sentiment_distribution": dist,
        "sentiment_percentages": pct,
        "frequent_aspects": frequent_aspects,
    }


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/scrape-and-analyze", response_model=ScrapeAnalyzeResponse)
async def scrape_and_analyze(request: ScrapeAnalyzeRequest):
    """
    **All-in-one pipeline:**

    1. Searches Google Maps for `business_name` (+ optional `location`)
    2. Scrapes up to `max_reviews` reviews using headless Chromium (no API key needed)
    3. Runs LLM analysis on every review
    4. Computes aggregate insights (sentiment distribution, top aspects, executive summary)
    5. Saves everything to in-memory history
    6. Returns the complete payload — enough for both the per-review table
       and the summary dashboard in a single HTTP call

    **Note:** This endpoint can take 30–120 seconds depending on `max_reviews`
    and network speed. Consider bumping your HTTP client timeout accordingly.
    """

    # Run in a thread to avoid the Windows Proactor/Selector event loop conflict with uvicorn.
    # The sync wrapper starts its own isolated event loop inside the thread.
    scrape_data = await asyncio.to_thread(
        scrape_sync,
        business_name=request.business_name,
        location=request.location,
        max_reviews=request.max_reviews,
        sort_by_newest=request.sort_by_newest,
    )

    scraped_reviews: list[dict] = scrape_data.get("reviews", [])

    # Hard failure: scraper returned nothing AND reported an error
    if not scraped_reviews and scrape_data.get("error"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Could not scrape reviews for '{request.business_name}': "
                f"{scrape_data['error']}"
            ),
        )

    if not scraped_reviews:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No reviews found for '{request.business_name}'"
                + (f" in '{request.location}'" if request.location else "")
                + ". Try a more specific location or a different spelling."
            ),
        )

    # ── Step 2: Analyse ──────────────────────────────────────────────────────
    review_texts = [r["text"] for r in scraped_reviews if r.get("text")]

    if not review_texts:
        raise HTTPException(
            status_code=422,
            detail="Scraped reviews contain no text. Only star-only ratings were found.",
        )

    batch_id = store.create_batch(source="scraper")

    try:
        raw_results = analyze_reviews_batch(review_texts)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    store.update_batch(batch_id, raw_results)
    batch = store.get_batch(batch_id)

    # ── Step 3: Summary ──────────────────────────────────────────────────────
    summary_stats = _build_summary(raw_results)

    try:
        insights = generate_batch_insights(raw_results)
    except Exception:
        insights = {
            "top_complaints": [],
            "top_praise": [],
            "executive_summary": (
                f"Analysed {len(raw_results)} reviews for "
                f"'{scrape_data.get('place_name') or request.business_name}'."
            ),
        }

    # ── Step 4: Average rating from raw scrape ───────────────────────────────
    ratings = [r["rating"] for r in scraped_reviews if r.get("rating") is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    # ── Step 5: Build response ───────────────────────────────────────────────
    results_out = [
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

    reviews_raw_out = [
        ScrapedReviewMeta(
            author=r.get("author", "Anonymous"),
            rating=r.get("rating"),
            date=r.get("date", ""),
            text=r.get("text", ""),
        )
        for r in scraped_reviews
        if r.get("text")  # only include reviews that were analysed
    ]

    return ScrapeAnalyzeResponse(
        # Scrape metadata
        business_name=request.business_name,
        location=request.location,
        place_name=scrape_data.get("place_name", request.business_name),
        place_url=scrape_data.get("place_url", ""),
        total_scraped=len(scraped_reviews),
        scrape_error=scrape_data.get("error"),

        # Batch
        batch_id=batch_id,
        status=batch["status"],
        created_at=batch["created_at"],
        completed_at=batch.get("completed_at"),

        # Per-review
        reviews_raw=reviews_raw_out,
        results=results_out,

        # Summary
        sentiment_distribution=summary_stats["sentiment_distribution"],
        sentiment_percentages=summary_stats["sentiment_percentages"],
        frequent_aspects=summary_stats["frequent_aspects"],
        top_complaints=insights.get("top_complaints", []),
        top_praise=insights.get("top_praise", []),
        executive_summary=insights.get("executive_summary", ""),
        average_rating=avg_rating,
    )
