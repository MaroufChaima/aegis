"""
UAVs router.

GET  /api/uavs         — returns all UAV current-state rows (dashboard initial load)
POST /api/uavs/update  — receives one UAV position tick from the simulator,
                         upserts the row, and broadcasts a uav_update WebSocket message
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.uav import UAVOut, UAVUpdateIn
from services.uav_service import upsert_uav, get_all_uavs
from websocket_manager import manager, _make_envelope

router = APIRouter(prefix="/api", tags=["uavs"])


@router.get("/uavs", response_model=list[UAVOut])
def list_uavs(db: Session = Depends(get_db)):
    """Return current position and status for all simulated UAVs.

    Used for the initial load of the UAV Fleet page. Real-time updates
    arrive via WebSocket ``uav_update`` messages.

    Args:
        db: Injected SQLAlchemy session.

    Returns:
        JSON array of UAVOut objects ordered by uav_id.
    """
    return get_all_uavs(db)


@router.post("/uavs/update", status_code=status.HTTP_200_OK)
async def update_uav(payload: UAVUpdateIn, db: Session = Depends(get_db)):
    """Receive one UAV position tick from the simulator.

    Upserts the UAV row and broadcasts a ``uav_update`` message to all
    connected dashboard clients so UAV markers reposition in real time.

    Args:
        payload: UAVUpdateIn parsed from the simulator's POST body.
        db:      Injected SQLAlchemy session.

    Returns:
        JSON confirmation with uav_id and current battery.
    """
    data   = payload.model_dump()
    record = upsert_uav(db, data)

    await manager.broadcast(
        _make_envelope("uav_update", {
            "uav_id":           record.uav_id,
            "latitude":         record.latitude,
            "longitude":        record.longitude,
            "altitude":         record.altitude,
            "battery":          record.battery,
            "status":           record.status,
            "coverage_radius":  record.coverage_radius,
            "connected_devices": record.connected_devices,
            "timestamp":        record.timestamp,
        })
    )

    return {"status": "ok", "uav_id": record.uav_id, "battery": record.battery}
