"""
Profile endpoints for the WBAN victim architecture. The /api/victims-new endpoint
will replace /api/victims in migration phase M6.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.profile_service import get_victim_with_profile, get_all_victims
from schemas.victim import VictimProfileOut, VictimSummaryOut

router = APIRouter()


@router.get("/api/victims/{victim_id}/profile", response_model=VictimProfileOut)
def victim_profile(victim_id: str, db: Session = Depends(get_db)):
    result = get_victim_with_profile(db, victim_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Victim {victim_id} not found")
    return result


@router.get("/api/victims-new", response_model=list[VictimSummaryOut])
def victims_new(db: Session = Depends(get_db)):
    return get_all_victims(db)
