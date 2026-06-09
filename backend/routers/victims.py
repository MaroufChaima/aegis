"""
Victims router — exposes registered device state to the dashboard.

Endpoint: GET /api/victims
Returns all devices pre-sorted by severity score so the frontend table
renders correctly on initial load before any WebSocket updates arrive.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.device import DeviceOut
from services.device_service import get_all_devices
from services.victim_state_service import get_all_victim_states, get_victim_state
from schemas.victim_state import VictimStateOut

router = APIRouter(prefix="/api", tags=["victims"])


@router.get("/victims", response_model=list[VictimStateOut])
def list_victims(db: Session = Depends(get_db)):
    """Return all registered devices with current status and latest AI scores.

    Used for the initial page load of the dashboard. Subsequent updates
    arrive via WebSocket push — this endpoint is not polled.

    Args:
        db: Injected SQLAlchemy session from get_db().

    Returns:
        JSON array of DeviceOut objects ordered by severity_score descending.
        Returns an empty array if no devices have been registered yet.
    """
    results = get_all_victim_states(db)
    return results


@router.get("/victims/{victim_id}", response_model=VictimStateOut)
def get_victim(victim_id: str, db: Session = Depends(get_db)):
    """Return the current state for one specific victim including identity fields."""
    result = get_victim_state(db, victim_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f'Victim {victim_id} not found or has not yet sent any packets')
    return result
