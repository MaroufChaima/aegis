"""
Victim lookup functions for the WBAN ingest pipeline. Uses raw SQL via text()
to avoid circular imports. No ORM model classes are imported directly.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text


def victim_exists(db: Session, victim_id: str) -> bool:
    """Checks whether a victim with this ID has been seeded into the database.
    The ingest pipeline uses this to reject packets from unknown victim IDs before
    attempting any processing."""

    result = db.execute(
        text("SELECT COUNT(*) FROM victims WHERE victim_id = :victim_id"),
        {"victim_id": victim_id},
    )
    return result.scalar() > 0


def get_victim_profile_for_pipeline(db: Session, victim_id: str) -> dict | None:
    """Returns victim identity and physiological profile combined in one query.
    Used by the AI pipeline to resolve personalized alert thresholds. Returns None
    if victim does not exist — callers must handle this case."""

    row = db.execute(
        text(
            "SELECT v.victim_id, v.risk_category, v.is_athlete, v.pregnancy_status, "
            "v.medical_conditions, "
            "vp.hr_normal_min, vp.hr_normal_max, "
            "vp.temp_normal_min, vp.temp_normal_max, "
            "vp.spo2_normal_min, "
            "vp.rr_normal_min, vp.rr_normal_max, "
            "vp.glucose_normal_min, vp.glucose_normal_max, "
            "vp.bp_systolic_normal_min, vp.bp_systolic_normal_max "
            "FROM victims v "
            "LEFT JOIN victim_physiological_profiles vp ON v.victim_id = vp.victim_id "
            "WHERE v.victim_id = :victim_id"
        ),
        {"victim_id": victim_id},
    ).first()

    if row is None:
        return None

    return dict(row._mapping)


def get_assigned_sensors(db: Session, victim_id: str) -> list:
    """Returns the list of sensor type IDs assigned to this victim. Used to calculate
    sensor_count_expected and identify which sensors should have reported in a packet."""

    rows = db.execute(
        text(
            "SELECT sensor_type_id FROM victim_sensors "
            "WHERE victim_id = :victim_id AND is_active = 1"
        ),
        {"victim_id": victim_id},
    ).fetchall()

    return [row[0] for row in rows]
