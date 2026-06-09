# LEGACY: Original flat preprocessing module. Preserved for the legacy /api/ingest router.
# New WBAN pipeline uses services/preprocessing/ package instead.
"""
Preprocessing pipeline functions applied to every incoming telemetry packet
before it is written to the database.

Call order enforced by the ingest router:
    1. validate_ranges  — already done by Pydantic; this adds explicit DB-safe checks
    2. deduplicate      — rejects duplicate packets within a 2-second window
    3. tag_signal_quality — annotates the dict with a poor_signal flag
"""

from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.telemetry import Telemetry


def validate_ranges(data: dict) -> None:
    """Raise HTTP 422 if any field violates its allowed range.

    Pydantic already enforces heart_rate and temperature on the schema model.
    This function provides an explicit, readable guard as a second layer so
    that service code calling the pipeline directly also benefits from the check.

    Args:
        data: Dict representation of a validated TelemetryIn payload.

    Raises:
        HTTPException 422: if heart_rate or temperature are out of range.
    """
    hr = data.get("heart_rate", 0)
    temp = data.get("temperature", 37.0)

    if not (0 <= hr <= 220):
        raise HTTPException(status_code=422, detail=f"heart_rate {hr} out of range 0–220")
    if not (30.0 <= temp <= 43.0):
        raise HTTPException(status_code=422, detail=f"temperature {temp} out of range 30–43")


def deduplicate(db: Session, data: dict) -> None:
    """Reject a packet if an identical device_id + timestamp already arrived within 2 seconds.

    Queries the telemetry table for any row from the same device whose stored
    timestamp is within ±2 seconds of the incoming packet's timestamp. If a
    match is found, raises HTTP 409 so the simulator knows the packet was
    discarded rather than silently lost.

    Args:
        db:   SQLAlchemy session.
        data: Dict representation of a validated TelemetryIn payload.

    Raises:
        HTTPException 409: if a duplicate packet is detected.
    """
    device_id = data["device_id"]
    try:
        incoming_ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    except ValueError:
        return  # unparseable timestamp — let later stages handle it

    window_start = (incoming_ts - timedelta(seconds=2)).isoformat()
    window_end   = (incoming_ts + timedelta(seconds=2)).isoformat()

    existing = (
        db.query(Telemetry)
        .filter(
            Telemetry.device_id == device_id,
            Telemetry.timestamp >= window_start,
            Telemetry.timestamp <= window_end,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate packet: {device_id} already recorded near {data['timestamp']}",
        )


def tag_signal_quality(data: dict) -> dict:
    """Annotate the packet dict with a poor_signal flag based on RSSI.

    RSSI below –100 dBm indicates a very weak LoRaWAN link that may produce
    unreliable readings. The flag is stored alongside the record so the
    dashboard can visually mark affected devices.

    Args:
        data: Dict representation of a validated TelemetryIn payload.

    Returns:
        The same dict with a 'poor_signal' key added (bool).
    """
    data["poor_signal"] = data.get("rssi", 0) < -100
    return data
