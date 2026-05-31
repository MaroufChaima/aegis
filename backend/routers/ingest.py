"""
Ingest router — receives telemetry packets from the simulator.

Single endpoint: POST /api/ingest
Pipeline: schema validation (Pydantic) → range check → deduplication
          → signal quality tagging → DB insert → 200 response.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.telemetry import TelemetryIn
from services.preprocessing import validate_ranges, deduplicate, tag_signal_quality
from services.telemetry_service import insert_telemetry
from services.device_service import upsert_device

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest(payload: TelemetryIn, db: Session = Depends(get_db)):
    """Accept one telemetry packet from the simulator and persist it.

    Processing steps (in order):
        1. Pydantic parses and validates the request body into TelemetryIn,
           rejecting malformed packets before this function is called.
        2. validate_ranges performs an explicit range guard as a second layer.
        3. deduplicate queries the DB and raises 409 if the packet is a duplicate.
        4. tag_signal_quality annotates the dict with a poor_signal flag.
        5. insert_telemetry writes the record to SQLite.

    Args:
        payload: Validated TelemetryIn parsed from the request body.
        db:      Injected SQLAlchemy session from get_db().

    Returns:
        JSON with device_id, timestamp, and the assigned row id.
    """
    data = payload.model_dump()

    validate_ranges(data)
    deduplicate(db, data)
    tag_signal_quality(data)

    record = insert_telemetry(db, data)
    upsert_device(db, data)

    return {
        "status": "ok",
        "device_id": record.device_id,
        "timestamp": record.timestamp,
        "id": record.id,
    }
