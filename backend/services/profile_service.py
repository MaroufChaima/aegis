"""
Database query functions for victim identity, physiological profiles, and sensor
assignments. This service uses raw SQL via text() to avoid circular imports — no
ORM model classes are imported directly.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text


def get_victim_with_profile(db: Session, victim_id: str) -> dict | None:
    """Returns complete victim information including personalized physiological
    thresholds and sensor assignments. Used by the triage scorer to resolve
    personalized alert thresholds."""

    victim_row = db.execute(
        text("SELECT * FROM victims WHERE victim_id = :victim_id"),
        {"victim_id": victim_id},
    ).mappings().first()

    if victim_row is None:
        return None

    result = dict(victim_row)

    profile_row = db.execute(
        text("SELECT * FROM victim_physiological_profiles WHERE victim_id = :victim_id"),
        {"victim_id": victim_id},
    ).mappings().first()

    profile_fields = [
        "profile_id", "hr_baseline", "hr_normal_min", "hr_normal_max",
        "spo2_normal_min", "temp_normal_min", "temp_normal_max",
        "rr_normal_min", "rr_normal_max", "glucose_normal_min",
        "glucose_normal_max", "bp_systolic_normal_min", "bp_systolic_normal_max",
        "notes", "updated_at",
    ]

    if profile_row is not None:
        result.update(dict(profile_row))
    else:
        for field in profile_fields:
            result[field] = None

    sensor_rows = db.execute(
        text("SELECT sensor_type_id FROM victim_sensors WHERE victim_id = :victim_id AND is_active = 1"),
        {"victim_id": victim_id},
    ).fetchall()

    assigned_sensors = [row[0] for row in sensor_rows]
    result["assigned_sensors"] = assigned_sensors
    result["assigned_sensor_count"] = len(assigned_sensors)

    return result


def get_all_victims(db: Session) -> list[dict]:
    """Returns all victims for the dashboard overview. Used for initial page load."""

    rows = db.execute(
        text("SELECT * FROM victims ORDER BY victim_id")
    ).mappings().fetchall()

    victims = []
    for row in rows:
        victim = dict(row)
        victim.setdefault("severity_score", 0)
        victims.append(victim)

    return victims


def get_victim_profile_only(db: Session, victim_id: str) -> dict | None:
    """Returns only the physiological profile for a victim. Used by the threshold
    engine to resolve personalized alert thresholds without loading all victim data."""

    row = db.execute(
        text("SELECT * FROM victim_physiological_profiles WHERE victim_id = :victim_id"),
        {"victim_id": victim_id},
    ).mappings().first()

    if row is None:
        return None

    return dict(row)
