"""
Victims router — exposes registered device state to the dashboard.

Endpoint: GET /api/victims
Returns all devices pre-sorted by severity score so the frontend table
renders correctly on initial load before any WebSocket updates arrive.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.device import DeviceOut
from services.device_service import get_all_devices

router = APIRouter(prefix="/api", tags=["victims"])


@router.get("/victims", response_model=list[DeviceOut])
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
    return get_all_devices(db)
