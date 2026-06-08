"""
Structural and range validation for incoming WBAN coordinator packets. All functions
take plain Python dicts or primitives and return plain results — no ORM models are
used here so this module can be tested independently of the database schema.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text


def validate_victim_known(db: Session, victim_id: str) -> tuple:
    """Checks that the victim_id in the packet exists in the database. Returns a
    tuple of (is_valid, error_message). error_message is None when valid."""

    result = db.execute(
        text("SELECT COUNT(*) FROM victims WHERE victim_id = :victim_id"),
        {"victim_id": victim_id},
    )
    if result.scalar() > 0:
        return (True, None)
    return (False, f"Unknown victim_id: {victim_id}")


def validate_packet_completeness(packet_dict: dict) -> tuple:
    """Validates the completeness metadata in the packet header. Does not validate
    individual readings — that happens in imputation_service."""

    completeness = packet_dict.get("packet_completeness", 0.0)
    if not (0.0 <= completeness <= 1.0):
        return (
            False,
            f"packet_completeness {completeness} is outside the valid range 0.0 to 1.0",
        )

    expected = packet_dict.get("sensor_count_expected", 0)
    received = packet_dict.get("sensor_count_received", 0)
    if received > expected:
        return (
            False,
            f"sensor_count_received ({received}) exceeds sensor_count_expected ({expected})",
        )

    return (True, None)


def validate_reading_ranges(readings: dict, db: Session) -> dict:
    """Performs global range validation on each sensor reading. Uses very permissive
    bounds (50 percent below min and 200 percent above max) to catch only obviously
    impossible values like negative heart rates or temperatures above 80 degrees.
    Personal range validation happens in the AI pipeline. Returns a dict of validity
    flags per sensor."""

    rows = db.execute(
        text(
            "SELECT sensor_type_id, normal_min_global, normal_max_global "
            "FROM sensor_types"
        )
    ).fetchall()

    sensor_bounds = {row[0]: (row[1], row[2]) for row in rows}

    validity = {}
    for sensor_type_id, value in readings.items():
        if value is None:
            validity[sensor_type_id] = True
            continue

        if sensor_type_id not in sensor_bounds:
            validity[sensor_type_id] = True
            continue

        normal_min, normal_max = sensor_bounds[sensor_type_id]
        lower_bound = normal_min * 0.5
        upper_bound = normal_max * 2.0

        if value < lower_bound or value > upper_bound:
            validity[sensor_type_id] = False
        else:
            validity[sensor_type_id] = True

    return validity
