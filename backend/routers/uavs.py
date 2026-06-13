from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas.uav import UAVOut, UAVUpdateIn
from services.uav_service import upsert_uav, get_all_uavs_enriched
from websocket_manager import manager, _make_envelope

router = APIRouter(prefix="/api", tags=["uavs"])


@router.get("/uavs", response_model=list[UAVOut])
def list_uavs(region: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return get_all_uavs_enriched(db, region=region)


@router.post("/uavs/update", status_code=status.HTTP_200_OK)
async def update_uav(payload: UAVUpdateIn, db: Session = Depends(get_db)):
    data = payload.model_dump()
    record = upsert_uav(db, data)
    enriched = get_all_uavs_enriched(db, region=record.current_region or record.home_region)
    row = next((u for u in enriched if u["uav_id"] == record.uav_id), None)

    ws_payload = row or {
        "uav_id": record.uav_id,
        "name": record.name,
        "home_region": record.home_region,
        "current_region": record.current_region,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "altitude": record.altitude,
        "battery": record.battery,
        "status": record.status,
        "coverage_radius": record.coverage_radius,
        "connected_devices": record.connected_devices,
        "timestamp": record.timestamp,
        "connected_users": [],
        "nearby_teams": 0,
    }

    await manager.broadcast(_make_envelope("uav_update", ws_payload))
    return {"status": "ok", "uav_id": record.uav_id, "battery": record.battery}
