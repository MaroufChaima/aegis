"""
Database operations for the devices table.

Rules:
- upsert_device   — called by the ingest pipeline on every packet
- get_all_devices — called by GET /api/victims
No other module writes to the devices table.
"""

from sqlalchemy.orm import Session

from models.device import Device


def upsert_device(db: Session, data: dict, ai_result: dict | None = None) -> Device:
    """Create or update the device record with the latest telemetry values.

    On first packet from a new device, inserts a new row. On subsequent
    packets, updates all mutable fields so the row always reflects the
    device's current state. Uses device_id as the natural unique key.

    Fields updated on every call: status, last_seen, uav_relay_id,
    and all latest vitals (latitude, longitude, heart_rate, temperature,
    sos_signal, movement, rssi, battery).

    When ``ai_result`` is provided, AI score fields (severity_score,
    priority_class, is_anomaly) are also updated so GET /api/victims
    returns current scores without a separate query.

    Args:
        db:        SQLAlchemy session.
        data:      Dict containing at minimum the fields produced by a
                   validated, preprocessed TelemetryIn payload.
        ai_result: Optional dict returned by ``run_ai_pipeline()``.
                   Keys used: severity_score, priority_class, is_anomaly.
                   When None, AI score columns are left unchanged.

    Returns:
        The Device ORM instance after commit.
    """
    device = db.query(Device).filter(Device.device_id == data["device_id"]).first()

    if device is None:
        device = Device(device_id=data["device_id"])
        db.add(device)

    device.status       = "sos" if data.get("sos_signal") else "online"
    device.last_seen    = data["timestamp"]
    device.uav_relay_id = data.get("uav_relay_id")
    device.latitude     = data.get("latitude")
    device.longitude    = data.get("longitude")
    device.heart_rate   = data.get("heart_rate")
    device.temperature  = data.get("temperature")
    device.sos_signal   = int(data.get("sos_signal", False))
    device.movement     = int(data.get("movement", True))
    device.rssi         = data.get("rssi")
    device.battery      = data.get("battery")

    if ai_result is not None:
        device.severity_score = ai_result.get("severity_score", device.severity_score)
        device.priority_class = ai_result.get("priority_class", device.priority_class)
        device.is_anomaly     = int(ai_result.get("is_anomaly", device.is_anomaly))

    db.commit()
    db.refresh(device)
    return device


def get_all_devices(db: Session) -> list[Device]:
    """Return all registered device rows ordered by severity score descending.

    The ordering means the frontend priority table is pre-sorted without
    needing a client-side sort on initial load.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of Device ORM instances, highest severity first.
    """
    return (
        db.query(Device)
        .order_by(Device.severity_score.desc())
        .all()
    )
