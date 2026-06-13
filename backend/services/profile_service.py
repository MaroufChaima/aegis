"""
Database query functions for victim identity, physiological profiles, and sensor assignments.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text


OPERATIONAL_RANGES = {
    "battery": {"min": 10, "max": 100, "unit": "%"},
    "rssi": {"min": -120, "max": -40, "unit": "dBm"},
    "ecg_hr_variability": {"min": 15, "max": 120, "unit": "ms"},
    "eeg_alert_index": {"min": 0, "max": 0.4, "unit": ""},
    "motion_activity": {"min": 0, "max": 1, "unit": ""},
    "fall_detected": {"min": 0, "max": 0, "unit": ""},
}

SENSOR_LABELS = {
    "heart_rate": "Heart Rate",
    "spo2": "SpO₂",
    "temperature": "Temperature",
    "respiratory_rate": "Respiratory Rate",
    "blood_pressure_systolic": "BP Systolic",
    "blood_pressure_diastolic": "BP Diastolic",
    "glucose": "Glucose",
    "ecg_hr_variability": "ECG HRV",
    "eeg_alert_index": "EEG Index",
    "battery": "Battery",
    "rssi": "RSSI",
    "motion_activity": "Motion",
    "fall_detected": "Fall Detect",
    "altitude_m": "Altitude",
    "gps_lat": "GPS Latitude",
    "gps_lon": "GPS Longitude",
}


def _build_sensor_ranges(profile: dict, assigned_sensors: list) -> list:
    rows = []
    for sensor_id in assigned_sensors:
        label = SENSOR_LABELS.get(sensor_id, sensor_id.replace("_", " ").title())
        range_str = None
        alert_str = None

        if sensor_id == "heart_rate" and profile.get("hr_normal_min") is not None:
            range_str = f"{profile['hr_normal_min']}–{profile['hr_normal_max']} bpm"
        elif sensor_id == "temperature" and profile.get("temp_normal_min") is not None:
            range_str = f"{profile['temp_normal_min']}–{profile['temp_normal_max']} °C"
        elif sensor_id == "spo2" and profile.get("spo2_normal_min") is not None:
            range_str = f"≥ {profile['spo2_normal_min']}%"
        elif sensor_id == "respiratory_rate" and profile.get("rr_normal_min") is not None:
            range_str = f"{profile['rr_normal_min']}–{profile['rr_normal_max']} br/min"
        elif sensor_id == "blood_pressure_systolic" and profile.get("bp_systolic_normal_min") is not None:
            range_str = f"{profile['bp_systolic_normal_min']}–{profile['bp_systolic_normal_max']} mmHg"
        elif sensor_id == "blood_pressure_diastolic":
            range_str = "55–90 mmHg"
        elif sensor_id == "glucose" and profile.get("glucose_normal_min") is not None:
            range_str = f"{profile['glucose_normal_min']}–{profile['glucose_normal_max']} mg/dL"
        elif sensor_id in OPERATIONAL_RANGES:
            op = OPERATIONAL_RANGES[sensor_id]
            unit = op.get("unit", "")
            range_str = f"{op['min']}–{op['max']}{(' ' + unit) if unit else ''}"
        elif sensor_id in ("gps_lat", "gps_lon", "altitude_m"):
            range_str = "Operational GPS/altitude"
        else:
            range_str = "—"

        rows.append({
            "sensor_type_id": sensor_id,
            "label": label,
            "normal_range": range_str,
            "alert_if": alert_str or "See triage thresholds",
        })
    return rows


def get_victim_with_profile(db: Session, victim_id: str) -> dict | None:
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
        text(
            "SELECT DISTINCT sensor_type_id FROM victim_sensors "
            "WHERE victim_id = :victim_id AND is_active = 1 "
            "ORDER BY sensor_type_id"
        ),
        {"victim_id": victim_id},
    ).fetchall()

    assigned_sensors = [row[0] for row in sensor_rows]
    result["assigned_sensors"] = assigned_sensors
    result["assigned_sensor_count"] = len(assigned_sensors)
    result["sensor_ranges"] = _build_sensor_ranges(result, assigned_sensors)

    return result


def get_all_victims(db: Session) -> list[dict]:
    rows = db.execute(text("SELECT * FROM victims ORDER BY victim_id")).mappings().fetchall()
    return [dict(row) for row in rows]


def get_victim_profile_only(db: Session, victim_id: str) -> dict | None:
    row = db.execute(
        text("SELECT * FROM victim_physiological_profiles WHERE victim_id = :victim_id"),
        {"victim_id": victim_id},
    ).mappings().first()
    if row is None:
        return None
    return dict(row)
