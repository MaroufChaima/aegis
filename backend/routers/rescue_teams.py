from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.rescue_team_service import get_all_teams, get_team, get_rescuer
from schemas.rescue_team import RescueTeamOut, RescuerDetailOut

router = APIRouter(prefix="/api/rescue-teams", tags=["rescue-teams"])


@router.get("", response_model=list[RescueTeamOut])
def list_teams(region: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return get_all_teams(db, region=region)


@router.get("/rescuer/{rescuer_id}", response_model=RescuerDetailOut)
def rescuer_detail(rescuer_id: str, db: Session = Depends(get_db)):
    rescuer = get_rescuer(db, rescuer_id)
    if not rescuer:
        raise HTTPException(status_code=404, detail=f"Rescuer {rescuer_id} not found")
    return rescuer


@router.get("/{team_id}", response_model=RescueTeamOut)
def team_detail(team_id: str, db: Session = Depends(get_db)):
    team = get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return team
