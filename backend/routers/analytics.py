"""
Analytics router.
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from services.analytics_service import get_summary, get_timeseries

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(
    scope: Literal["global", "regional"] = Query("global"),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return get_summary(db, scope=scope, region=region)


@router.get("/timeseries")
def analytics_timeseries(db: Session = Depends(get_db)):
    return {"bins": get_timeseries(db)}
