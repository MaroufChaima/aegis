"""
Analytics router.

GET /api/analytics/summary    — aggregated stats for the analytics page cards
GET /api/analytics/timeseries — alert frequency binned by 5-minute intervals,
                                last 60 minutes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.analytics_service import get_summary, get_timeseries

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db)):
    """Return aggregated statistics for the analytics dashboard.

    Includes victim counts by priority and status, alert counts by type
    (last 60 minutes), average vitals, UAV availability, and an estimated
    network coverage percentage.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        JSON dict matching the API_FLOW.md summary response shape.
    """
    return get_summary(db)


@router.get("/timeseries")
def analytics_timeseries(db: Session = Depends(get_db)):
    """Return alert counts binned into 5-minute intervals for the last hour.

    Always returns all 12 buckets so the Recharts BarChart has a fixed
    x-axis even when no alerts were generated in some intervals.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        JSON with ``bins`` list; each bin has ``timestamp``, ``count``,
        and ``critical_count``.
    """
    return {"bins": get_timeseries(db)}
