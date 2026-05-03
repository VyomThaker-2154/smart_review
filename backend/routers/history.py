from typing import Optional
from fastapi import APIRouter, Query

from models import HistoryResponse
from storage import store

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Records per page"),
    date_from: Optional[str] = Query(
        default=None,
        description="ISO 8601 date filter start, e.g. 2024-06-01",
    ),
    date_to: Optional[str] = Query(
        default=None,
        description="ISO 8601 date filter end, e.g. 2024-06-30",
    ),
):
    """
    Retrieve paginated review analysis history.

    Supports optional date range filtering using ISO 8601 date strings.
    Results are ordered most-recent first.
    """
    result = store.get_history(
        page=page,
        limit=limit,
        date_from=date_from,
        date_to=date_to,
    )
    return HistoryResponse(**result)
