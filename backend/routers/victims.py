from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas.victim_state import VictimStateOut
from services.victim_state_service import get_all_victim_states, get_victim_state

router = APIRouter(prefix="/api", tags=["victims"])


@router.get("/victims", response_model=list[VictimStateOut])
def list_victims(region: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return get_all_victim_states(db, region=region)


@router.get("/victims/{victim_id}", response_model=VictimStateOut)
def get_victim(victim_id: str, db: Session = Depends(get_db)):
    result = get_victim_state(db, victim_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f'User {victim_id} not found or has not yet sent any packets',
        )
    return result
