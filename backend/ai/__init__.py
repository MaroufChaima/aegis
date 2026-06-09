"""
AI pipeline entry point for the AEGIS WBAN backend.

Exports a single function, run_ai_pipeline, that chains all AI modules using
personalized victim profiles and thresholds. All AI internals are hidden behind
this interface — the ingest router calls only this function.
"""

from ai.threshold_engine import resolve_thresholds, check_global_anomaly, check_personal_anomaly
from ai.triage_scorer import compute_severity_score, classify_priority
from ai.detector_registry import predict as detect_anomaly
from ai.alert_generator import decide_alerts


def run_ai_pipeline(
    victim_id: str,
    readings_dict: dict,
    victim_profile: dict,
    sos_active: bool = False,
    seconds_without_movement: float = 0,
    seconds_offline: float = 0,
) -> dict:
    """Runs the complete AI pipeline for one coordinator packet. Takes the victim_id,
    their current readings (already imputed), and their physiological profile. Returns
    a comprehensive result dict containing triage score, priority class, anomaly
    detection result, per-sensor anomaly flags for both global and personal standards,
    and any alerts to be generated. This is the only function the ingest router calls —
    all AI internals are hidden behind this interface."""

    # STEP 1 — Resolve personalized thresholds
    thresholds = resolve_thresholds(victim_profile)

    # STEP 2 — Per-sensor anomaly flags (global and personal)
    global_flags   = {}
    personal_flags = {}
    for sensor_type_id, value in readings_dict.items():
        if value is not None:
            global_flags[sensor_type_id]   = check_global_anomaly(sensor_type_id, value)
            personal_flags[sensor_type_id] = check_personal_anomaly(sensor_type_id, value, thresholds)
        else:
            global_flags[sensor_type_id]   = False
            personal_flags[sensor_type_id] = False

    # STEP 3 — Personalized anomaly detection
    anomaly_result = detect_anomaly(victim_id, readings_dict)

    # STEP 4 — Triage scoring using personalized thresholds
    severity_score = compute_severity_score(
        readings_dict,
        thresholds,
        sos_active,
        seconds_without_movement,
        seconds_offline,
    )

    # STEP 5 — Priority classification
    priority_class = classify_priority(severity_score)

    # STEP 6 — Alert generation
    triage_result = {
        "severity_score": severity_score,
        "priority_class": priority_class,
    }
    alerts = decide_alerts(
        victim_id,
        readings_dict,
        thresholds,
        triage_result,
        anomaly_result,
        sos_active,
        victim_profile,
    )

    # STEP 7 — Return full pipeline result
    return {
        "severity_score":        severity_score,
        "priority_class":        priority_class,
        "is_anomaly":            anomaly_result["is_anomaly"],
        "anomaly_score":         anomaly_result["anomaly_score"],
        "anomaly_confidence":    anomaly_result["confidence"],
        "detector_status":       anomaly_result["detector_status"],
        "global_anomaly_flags":  global_flags,
        "personal_anomaly_flags": personal_flags,
        "thresholds_used":       thresholds,
        "alerts":                alerts,
    }


__all__ = ["run_ai_pipeline"]
