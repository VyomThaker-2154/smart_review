from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


# ── Shared sub-models ─────────────────────────────────────────────────────────

class AspectSentiment(BaseModel):
    aspect: str
    sentiment: str  # positive | negative | neutral
    score: Optional[float] = None


class ReviewAnalysisResult(BaseModel):
    text: str
    sentiment: str                          # positive | negative | neutral | mixed
    confidence: float = Field(ge=0.0, le=1.0)
    aspects: List[AspectSentiment] = []
    summary: str
    suggested_reply: str
    key_phrases: List[str] = []
    error: Optional[str] = None             # populated only on per-review failures


# ── /analyze ──────────────────────────────────────────────────────────────────

class SingleReviewRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=5000)

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class SingleReviewResponse(ReviewAnalysisResult):
    id: str
    created_at: str


# ── /bulk-analyze ─────────────────────────────────────────────────────────────

class BulkReviewRequest(BaseModel):
    reviews: List[str] = Field(..., min_length=1)

    @field_validator("reviews")
    @classmethod
    def validate_reviews(cls, v):
        cleaned = [r.strip() for r in v if r.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty review is required")
        return cleaned


class BulkReviewResponse(BaseModel):
    batch_id: str
    total: int
    status: str
    results: List[ReviewAnalysisResult]
    created_at: str
    completed_at: Optional[str] = None


# ── /summary/{batch_id} ───────────────────────────────────────────────────────

class SentimentDistribution(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    mixed: int = 0


class AspectFrequency(BaseModel):
    aspect: str
    count: int
    positive_count: int = 0
    negative_count: int = 0


class SummaryResponse(BaseModel):
    batch_id: str
    total_reviews: int
    sentiment_distribution: SentimentDistribution
    sentiment_percentages: Dict[str, float] = {}
    top_complaints: List[str]
    top_praise: List[str]
    frequent_aspects: List[AspectFrequency]
    executive_summary: str
    created_at: str


# ── /history ──────────────────────────────────────────────────────────────────

class HistoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    records: List[Dict[str, Any]]


# ── /upload-csv ───────────────────────────────────────────────────────────────

class UploadCSVResponse(BaseModel):
    batch_id: str
    status: str
    total_rows: int
    message: str


# ── /generate-reply ───────────────────────────────────────────────────────────

class GenerateReplyRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=5000)
    sentiment: Optional[str] = None         # pre-computed if available
    business_name: Optional[str] = None     # personalise the reply
    tone: Optional[str] = "professional"    # professional | friendly | apologetic


class GenerateReplyResponse(BaseModel):
    original_review: str
    suggested_reply: str
    tone: str
