"""
Rule-based triage scorer for the AEGIS WBAN AI pipeline.

Pure functions only — no database access, no side effects, no external imports.
All threshold comparisons use the personalized thresholds dict from threshold_engine.py
rather than hardcoded values, enabling victim-specific triage scoring.
"""


def compute_severity_score(
    readings_dict: dict,
    thresholds: dict,
    sos_active: bool = False,
    seconds_without_movement: float = 0,
    seconds_offline: float = 0,
) -> int:
    """Computes a severity score from 0 to 100 using personalized thresholds from the
    victim profile. Every threshold comparison uses the thresholds dict rather than
    hardcoded values so that an athlete with cardiac_low_hr of 36.1 is not penalized
    for their naturally lower heart rate. The score is capped at 100 because multiple
    simultaneous critical conditions can otherwise exceed 100."""

    score = 0

    # SOS
    if sos_active:
        score += 55

    heart_rate = readings_dict.get("heart_rate")
    if heart_rate is not None and heart_rate < thresholds.get("cardiac_low_hr", 40.0):
        score += 40
    if heart_rate is not None and heart_rate > thresholds.get("cardiac_high_hr", 150.0):
        score += 20

    temperature = readings_dict.get("temperature")
    if temperature is not None and temperature < thresholds.get("hypothermia_temp", 35.0):
        score += 25
    if temperature is not None and temperature > thresholds.get("hyperthermia_temp", 39.5):
        score += 15

    spo2 = readings_dict.get("spo2")
    if spo2 is not None and spo2 < thresholds.get("low_spo2", 90.0):
        score += 20

    respiratory_rate = readings_dict.get("respiratory_rate")
    if respiratory_rate is not None and respiratory_rate < thresholds.get("low_rr", 8.0):
        score += 20
    if respiratory_rate is not None and respiratory_rate > thresholds.get("high_rr", 25.0):
        score += 10

    glucose = readings_dict.get("glucose")
    if glucose is not None and thresholds.get("low_glucose") is not None and glucose < thresholds["low_glucose"]:
        score += 30
    if glucose is not None and thresholds.get("high_glucose") is not None and glucose > thresholds["high_glucose"]:
        score += 20

    if seconds_without_movement >= 1200:
        score += 30
    elif seconds_without_movement >= 600:
        score += 25
    elif seconds_without_movement >= 300:
        score += 10

    if seconds_offline >= 300:
        score += 30

    battery = readings_dict.get("battery")
    if battery is not None and battery < 10.0:
        score += 5

    rssi = readings_dict.get("rssi")
    if rssi is not None and rssi < -100.0:
        score += 10

    return min(100, score)


def classify_priority(score: int) -> str:
    """Maps severity score to triage priority class. P1 requires immediate intervention.
    P2 requires urgent attention. P3 is stable and can wait."""

    if score >= 70:
        return "P1"
    if score >= 40:
        return "P2"
    return "P3"
