"""
Database write operations for the alerts table.
This is the only module allowed to INSERT into the alerts table.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.alert import Alert


def create_alert(db: Session, alert_dict: dict) -> Alert:
    """Persist one alert record produced by the alert generator.

    Sets ``timestamp`` to the current UTC time at insert so the dashboard
    alert feed shows when the server generated the alert, not when the
    telemetry was emitted.

    Args:
        db:         SQLAlchemy session — caller is responsible for lifecycle.
        alert_dict: Dict returned by ``alert_generator.decide_alerts()``.
                    Required keys: device_id, alert_type, severity, message.
                    Optional key: ai_confidence (defaults to 1.0 for
                    rule-based alerts).

    Returns:
        The newly created Alert ORM instance with its auto-assigned id.
    """
    device_id = alert_dict.get("victim_id") or alert_dict.get("device_id", "UNKNOWN")
    record = Alert(
        device_id    = device_id,
        timestamp    = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        alert_type   = alert_dict["alert_type"],
        severity     = alert_dict["severity"],
        message      = alert_dict["message"],
        acknowledged = 0,
        ai_confidence = float(alert_dict.get("ai_confidence", 1.0)),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
