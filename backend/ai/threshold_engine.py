"""
Resolves personalized alert thresholds for each victim based on their physiological
profile. Applies safety margins to prevent alert flooding from minor measurement noise.
Pure Python — no external dependencies, no database access.
"""

# Population-level thresholds used when no personal profile is available.
# Based on standard clinical emergency thresholds.
GLOBAL_FALLBACK_THRESHOLDS = {
    "cardiac_low_hr":      50.0,
    "cardiac_high_hr":     150.0,
    "hypothermia_temp":    35.0,
    "hyperthermia_temp":   39.5,
    "low_spo2":            90.0,
    "low_rr":              8.0,
    "high_rr":             25.0,
    "low_glucose":         60.0,
    "high_glucose":        200.0,
    "low_bp_systolic":     80.0,
    "high_bp_systolic":    160.0,
}


def resolve_thresholds(victim_profile: dict) -> dict:
    """Resolves personalized alert thresholds for a specific victim based on their
    physiological profile. Applies a 5 percent safety margin to each threshold to
    prevent alert flooding from minor measurement noise. For example, an athlete with
    hr_normal_min of 38 gets a cardiac_low_hr threshold of 36.1, meaning their HR must
    drop below 36.1 before triggering a cardiac alert. A healthy adult with hr_normal_min
    of 55 gets a threshold of 52.25."""

    if victim_profile is None:
        result = dict(GLOBAL_FALLBACK_THRESHOLDS)
        result["source"] = "global_fallback"
        return result

    hr_min   = victim_profile.get("hr_normal_min")
    hr_max   = victim_profile.get("hr_normal_max")
    temp_min = victim_profile.get("temp_normal_min")
    temp_max = victim_profile.get("temp_normal_max")
    spo2_min = victim_profile.get("spo2_normal_min")
    rr_min   = victim_profile.get("rr_normal_min")
    rr_max   = victim_profile.get("rr_normal_max")
    glc_min  = victim_profile.get("glucose_normal_min")
    glc_max  = victim_profile.get("glucose_normal_max")
    bp_min   = victim_profile.get("bp_systolic_normal_min")
    bp_max   = victim_profile.get("bp_systolic_normal_max")

    return {
        "cardiac_low_hr":    hr_min  * 0.95 if hr_min  is not None else 40.0,
        "cardiac_high_hr":   hr_max  * 1.05 if hr_max  is not None else 150.0,
        "hypothermia_temp":  temp_min * 0.98 if temp_min is not None else 35.0,
        "hyperthermia_temp": temp_max * 1.02 if temp_max is not None else 39.5,
        "low_spo2":          spo2_min * 0.97 if spo2_min is not None else 90.0,
        "low_rr":            rr_min  * 0.90 if rr_min  is not None else 8.0,
        "high_rr":           rr_max  * 1.10 if rr_max  is not None else 25.0,
        "low_glucose":       glc_min * 0.90 if glc_min is not None else None,
        "high_glucose":      glc_max * 1.10 if glc_max is not None else None,
        "low_bp_systolic":   bp_min  * 0.92 if bp_min  is not None else 80.0,
        "high_bp_systolic":  bp_max  * 1.08 if bp_max  is not None else 160.0,
        "source":            "personal_profile",
    }


def check_global_anomaly(sensor_type_id: str, value: float) -> bool:
    """Checks whether a value is anomalous according to population-level thresholds.
    Used to set is_anomaly_global flag in telemetry_readings."""

    g = GLOBAL_FALLBACK_THRESHOLDS

    if sensor_type_id == "heart_rate":
        return value < g["cardiac_low_hr"] or value > g["cardiac_high_hr"]

    if sensor_type_id == "temperature":
        return value < g["hypothermia_temp"] or value > g["hyperthermia_temp"]

    if sensor_type_id == "spo2":
        return value < g["low_spo2"]

    if sensor_type_id == "respiratory_rate":
        return value < g["low_rr"] or value > g["high_rr"]

    if sensor_type_id == "glucose":
        return value < g["low_glucose"] or value > g["high_glucose"]

    if sensor_type_id == "blood_pressure_systolic":
        return value < g["low_bp_systolic"] or value > g["high_bp_systolic"]

    return False


def check_personal_anomaly(sensor_type_id: str, value: float, thresholds: dict) -> bool:
    """Checks whether a value is anomalous according to this specific victims
    personalized thresholds. Used to set is_anomaly_personal flag in
    telemetry_readings. A value can be globally anomalous but personally normal
    (athlete low HR) or globally normal but personally anomalous (hypertensive
    patient BP drop)."""

    if sensor_type_id == "heart_rate":
        low  = thresholds.get("cardiac_low_hr")
        high = thresholds.get("cardiac_high_hr")
        if low is None or high is None:
            return False
        return value < low or value > high

    if sensor_type_id == "temperature":
        low  = thresholds.get("hypothermia_temp")
        high = thresholds.get("hyperthermia_temp")
        if low is None or high is None:
            return False
        return value < low or value > high

    if sensor_type_id == "spo2":
        low = thresholds.get("low_spo2")
        if low is None:
            return False
        return value < low

    if sensor_type_id == "respiratory_rate":
        low  = thresholds.get("low_rr")
        high = thresholds.get("high_rr")
        if low is None or high is None:
            return False
        return value < low or value > high

    if sensor_type_id == "glucose":
        low  = thresholds.get("low_glucose")
        high = thresholds.get("high_glucose")
        if low is None or high is None:
            return False
        return value < low or value > high

    if sensor_type_id == "blood_pressure_systolic":
        low  = thresholds.get("low_bp_systolic")
        high = thresholds.get("high_bp_systolic")
        if low is None or high is None:
            return False
        return value < low or value > high

    return False
