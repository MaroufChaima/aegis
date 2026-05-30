"""
Database write operations for the telemetry table.
This is the only module allowed to INSERT into the telemetry table.
"""

from sqlalchemy.orm import Session

from models.telemetry import Telemetry


def insert_telemetry(db: Session, data: dict) -> Telemetry:
    """Insert one telemetry record and return the persisted ORM object.

    Converts boolean fields from Python bool to SQLite INTEGER (0/1) before
    inserting. Fields added by preprocessing (e.g. poor_signal) are not ORM
    columns and are intentionally excluded via the explicit field mapping.

    Args:
        db:   SQLAlchemy session — caller is responsible for lifecycle.
        data: Dict containing all fields of a validated, pre-processed
              TelemetryIn payload.

    Returns:
        The newly created Telemetry instance with its auto-assigned id populated.
    """
    record = Telemetry(
        device_id      = data["device_id"],
        timestamp      = data["timestamp"],
        latitude       = data["latitude"],
        longitude      = data["longitude"],
        heart_rate     = data["heart_rate"],
        temperature    = data["temperature"],
        sos_signal     = int(data["sos_signal"]),
        movement       = int(data["movement"]),
        rssi           = data["rssi"],
        snr            = data["snr"],
        battery        = data["battery"],
        is_anomaly     = 0,
        severity_score = 0,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
