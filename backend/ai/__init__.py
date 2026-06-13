"""
AI pipeline entry point for the AEGIS WBAN backend.
"""

from ai.threshold_engine import resolve_thresholds, check_global_anomaly, check_personal_anomaly
from ai.triage_scorer import compute_severity_score, classify_priority
from ai.detector_registry import predict as detect_anomaly
from ai.alert_generator import decide_alerts


def run_ai_pipeline(
    victim_id: str,
    readings_dict: dict,
    victim_profile: dict,
    seconds_without_movement: float = 0,
    seconds_offline: float = 0,
) -> dict:
    thresholds = resolve_thresholds(victim_profile)

    global_flags   = {}
    personal_flags = {}
    for sensor_type_id, value in readings_dict.items():
        if value is not None:
            global_flags[sensor_type_id]   = check_global_anomaly(sensor_type_id, value)
            personal_flags[sensor_type_id] = check_personal_anomaly(sensor_type_id, value, thresholds)
        else:
            global_flags[sensor_type_id]   = False
            personal_flags[sensor_type_id] = False

    anomaly_result = detect_anomaly(victim_id, readings_dict)

    severity_score = compute_severity_score(
        readings_dict,
        thresholds,
        seconds_without_movement,
        seconds_offline,
    )

    priority_class = classify_priority(severity_score)

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
        victim_profile,
    )

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
