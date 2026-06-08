"""
Core imputation module for missing WBAN sensor readings. Fills missing values using
three strategies in priority order: forward fill (recent history), KNN (other victims),
profile mean (personal normal range). All functions take plain Python dicts as input
and return plain Python dicts — no ORM models are imported here.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

# Module-level cache: {victim_id: {sensor_type_id: (value, timestamp_string)}}.
# Updated after each successful packet. Used by KNN imputation to find similar victims.
_recent_readings: dict = {}


def update_recent_readings_cache(victim_id: str, readings: dict, timestamp: str) -> None:
    """Updates the module-level cache of recent readings for KNN imputation. Called
    after every successful packet storage. Only non-None values are cached because we
    want the last known good reading, not a failed reading."""

    if victim_id not in _recent_readings:
        _recent_readings[victim_id] = {}

    for sensor_type_id, value in readings.items():
        if value is not None:
            _recent_readings[victim_id][sensor_type_id] = (value, timestamp)


def _forward_fill(
    db: Session,
    victim_id: str,
    sensor_type_id: str,
    current_timestamp: str,
    sensor_status: str,
) -> tuple:
    """Attempts forward fill imputation by using the most recent known good value for
    this sensor. Not used for damaged sensors. Returns None if no recent history exists
    or if the last reading is more than 120 seconds old."""

    if sensor_status == "damaged":
        return (None, "skipped_damaged")

    row = db.execute(
        text(
            "SELECT raw_value, timestamp FROM telemetry_readings "
            "WHERE victim_id = :victim_id AND sensor_type_id = :sensor_type_id "
            "AND raw_value_present = 1 "
            "ORDER BY timestamp DESC LIMIT 1"
        ),
        {"victim_id": victim_id, "sensor_type_id": sensor_type_id},
    ).first()

    if row is None:
        return (None, "no_history")

    try:
        past_dt = datetime.fromisoformat(row[1].rstrip("Z"))
        current_dt = datetime.fromisoformat(current_timestamp.rstrip("Z"))
        seconds_ago = abs((current_dt - past_dt).total_seconds())
    except (ValueError, AttributeError):
        return (None, "no_history")

    if seconds_ago > 120:
        return (None, "too_old")

    return (row[0], "forward_fill")


def _profile_mean(db: Session, victim_id: str, sensor_type_id: str) -> tuple:
    """Imputes a missing value using the midpoint of this victims personal physiological
    normal range. Used when forward fill is unavailable or inappropriate. More accurate
    than a global mean because it uses the victims individual profile."""

    row = db.execute(
        text(
            "SELECT vp.hr_normal_min, vp.hr_normal_max, "
            "vp.temp_normal_min, vp.temp_normal_max, "
            "vp.spo2_normal_min, "
            "vp.rr_normal_min, vp.rr_normal_max, "
            "vp.glucose_normal_min, vp.glucose_normal_max, "
            "vp.bp_systolic_normal_min, vp.bp_systolic_normal_max "
            "FROM victim_physiological_profiles vp "
            "WHERE vp.victim_id = :victim_id"
        ),
        {"victim_id": victim_id},
    ).first()

    if row is None:
        return (None, "no_profile")

    (
        hr_normal_min, hr_normal_max,
        temp_normal_min, temp_normal_max,
        spo2_normal_min,
        rr_normal_min, rr_normal_max,
        glucose_normal_min, glucose_normal_max,
        bp_systolic_normal_min, bp_systolic_normal_max,
    ) = row

    if sensor_type_id == "heart_rate":
        return ((hr_normal_min + hr_normal_max) / 2, "profile_mean")

    if sensor_type_id == "temperature":
        return ((temp_normal_min + temp_normal_max) / 2, "profile_mean")

    if sensor_type_id == "spo2":
        return ((spo2_normal_min + 100.0) / 2, "profile_mean")

    if sensor_type_id == "respiratory_rate":
        return ((rr_normal_min + rr_normal_max) / 2, "profile_mean")

    if sensor_type_id == "glucose":
        if glucose_normal_min is None:
            return (None, "not_applicable")
        return ((glucose_normal_min + glucose_normal_max) / 2, "profile_mean")

    if sensor_type_id == "blood_pressure_systolic":
        return ((bp_systolic_normal_min + bp_systolic_normal_max) / 2, "profile_mean")

    if sensor_type_id == "motion_activity":
        return (0.3, "profile_mean")

    if sensor_type_id == "fall_detected":
        return (0.0, "profile_mean")

    if sensor_type_id == "battery":
        return (None, "not_imputable")

    if sensor_type_id == "rssi":
        return (-85.0, "profile_mean")

    return (None, "not_imputable")


def _knn_impute(victim_id: str, sensor_type_id: str) -> tuple:
    """Simplified KNN imputation using the mean of the same sensor reading from all
    other currently active victims. Requires at least 3 other victims to have reported
    this sensor recently. Returns None if fewer than 3 neighbors are available. This is
    a simplified version of KNN that uses all available neighbors rather than selecting
    the K most similar ones."""

    other_values = [
        _recent_readings[s][sensor_type_id][0]
        for s in _recent_readings
        if s != victim_id and sensor_type_id in _recent_readings[s]
    ]

    if len(other_values) < 3:
        return (None, "insufficient_neighbors")

    mean_value = sum(other_values) / len(other_values)
    return (mean_value, "knn")


def impute_missing_readings(
    db: Session,
    victim_id: str,
    readings: dict,
    sensor_statuses: dict,
    timestamp: str,
) -> dict:
    """Main imputation function. Processes all readings in a packet and fills missing
    values using a three-stage priority strategy: forward fill first (uses recent
    history), then KNN (uses other victims), then profile mean (uses this victims
    personal normal range). Returns enriched readings with imputation metadata for
    every sensor."""

    if sensor_statuses is None:
        sensor_statuses = {}

    result = {}

    for sensor_type_id, value in readings.items():
        if value is not None:
            result[sensor_type_id] = {
                "raw_value":            value,
                "imputed_value":        None,
                "imputation_method":    None,
                "imputation_confidence": 1.0,
            }
            continue

        sensor_status = sensor_statuses.get(sensor_type_id, "unknown")

        # Stage 1 — forward fill
        ff_value, ff_method = _forward_fill(
            db, victim_id, sensor_type_id, timestamp, sensor_status
        )
        if ff_value is not None:
            result[sensor_type_id] = {
                "raw_value":            None,
                "imputed_value":        ff_value,
                "imputation_method":    ff_method,
                "imputation_confidence": 0.0,
            }
            continue

        # Stage 2 — KNN
        knn_value, knn_method = _knn_impute(victim_id, sensor_type_id)
        if knn_value is not None:
            result[sensor_type_id] = {
                "raw_value":            None,
                "imputed_value":        knn_value,
                "imputation_method":    knn_method,
                "imputation_confidence": 0.0,
            }
            continue

        # Stage 3 — profile mean
        pm_value, pm_method = _profile_mean(db, victim_id, sensor_type_id)
        if pm_value is not None:
            result[sensor_type_id] = {
                "raw_value":            None,
                "imputed_value":        pm_value,
                "imputation_method":    pm_method,
                "imputation_confidence": 0.0,
            }
            continue

        # All three strategies failed
        result[sensor_type_id] = {
            "raw_value":            None,
            "imputed_value":        None,
            "imputation_method":    "unresolvable",
            "imputation_confidence": 0.0,
        }

    return result
