"""
Ingest router — receives telemetry packets from the simulator.

Single endpoint: POST /api/ingest
Pipeline: schema validation (Pydantic) → range check → deduplication
          → signal quality tagging → DB insert → AI pipeline
          → device upsert (with AI scores) → alert persistence → 200 response.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.telemetry import TelemetryIn
from services.preprocessing_legacy import validate_ranges, deduplicate, tag_signal_quality
from services.telemetry_service import insert_telemetry
from services.device_service import upsert_device
from services.alert_service import create_alert
from ai import run_ai_pipeline
from websocket_manager import manager, make_telemetry_update, make_alert_message

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", status_code=status.HTTP_200_OK)
async def ingest(payload: TelemetryIn, db: Session = Depends(get_db)):
    """Accept one telemetry packet from the simulator and persist it.

    Processing steps (in order):
        1. Pydantic parses and validates the request body into TelemetryIn,
           rejecting malformed packets before this function is called.
        2. validate_ranges performs an explicit range guard as a second layer.
        3. deduplicate queries the DB and raises 409 if the packet is a duplicate.
        4. tag_signal_quality annotates the dict with a poor_signal flag.
        5. insert_telemetry writes the raw telemetry row to SQLite.
        6. run_ai_pipeline scores the packet (triage + anomaly + alert decisions).
        7. upsert_device writes current vitals and AI scores to the devices table.
        8. create_alert persists each alert produced by the pipeline.

    Args:
        payload: Validated TelemetryIn parsed from the request body.
        db:      Injected SQLAlchemy session from get_db().

    Returns:
        JSON with device_id, timestamp, row id, severity_score, priority_class,
        and alert count.
    """
    data = payload.model_dump()

    validate_ranges(data)
    deduplicate(db, data)
    tag_signal_quality(data)

    record    = insert_telemetry(db, data)
    ai_result = run_ai_pipeline(data, db)
    upsert_device(db, data, ai_result)

    # Broadcast telemetry update to all connected dashboard clients
    await manager.broadcast(make_telemetry_update(data, ai_result))

    # Persist and broadcast each alert produced by the AI pipeline
    for alert_dict in ai_result["alerts"]:
        alert_record = create_alert(db, alert_dict)
        await manager.broadcast(make_alert_message(alert_record))

    return {
        "status":         "ok",
        "device_id":      record.device_id,
        "timestamp":      record.timestamp,
        "id":             record.id,
        "severity_score": ai_result["severity_score"],
        "priority_class": ai_result["priority_class"],
        "alert_count":    len(ai_result["alerts"]),
    }
