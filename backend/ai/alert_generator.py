"""
Alert generator for the AEGIS WBAN AI pipeline.

Pure functions only — no database access, no external imports beyond stdlib.
All threshold comparisons use the personalized thresholds dict from threshold_engine.py.
The is_personal_alert flag on each alert distinguishes personalized from global decisions.
"""

import time

# {(victim_id, alert_type): last_alert_timestamp_float}. Prevents flooding same alert repeatedly.
_cooldown_cache: dict = {}

COOLDOWN_SECONDS = 300


def _is_on_cooldown(victim_id: str, alert_type: str) -> bool:
    key = (victim_id, alert_type)
    cached_time = _cooldown_cache.get(key)
    if cached_time is not None and (time.time() - cached_time) < COOLDOWN_SECONDS:
        return True
    return False


def _record_alert(victim_id: str, alert_type: str) -> None:
    _cooldown_cache[(victim_id, alert_type)] = time.time()


def decide_alerts(
    victim_id: str,
    readings_dict: dict,
    thresholds: dict,
    triage_result: dict,
    anomaly_result: dict,
    victim_profile: dict,
) -> list:
    """Generates alert records based on triage results, anomaly detection, and
    personalized thresholds. The is_personal_alert flag distinguishes alerts triggered
    by personal profile thresholds from alerts triggered by global thresholds. This flag
    enables the research finding that personalized assessment generates different alert
    patterns than global assessment for the same measurements."""

    alerts = []

    def _emit(alert_type, severity, message, ai_confidence, is_personal_alert):
        if _is_on_cooldown(victim_id, alert_type):
            return
        alerts.append({
            "victim_id":         victim_id,
            "alert_type":        alert_type,
            "severity":          severity,
            "message":           message,
            "ai_confidence":     ai_confidence,
            "is_personal_alert": is_personal_alert,
        })
        _record_alert(victim_id, alert_type)

    # ALERT 1 — P1 classification
    if triage_result.get("priority_class") == "P1" and triage_result.get("severity_score", 0) >= 70:
        risk_cat = victim_profile.get("risk_category", "unknown") if victim_profile else "unknown"
        _emit(
            alert_type="p1_classification",
            severity="critical",
            message=(
                f"{victim_id}: Severity score {triage_result['severity_score']} — "
                f"classified P1 IMMEDIATE. Personal profile: {risk_cat}"
            ),
            ai_confidence=0.95,
            is_personal_alert=True,
        )

    # ALERT 3 — Cardiac low HR (personal)
    heart_rate = readings_dict.get("heart_rate")
    is_personal = thresholds.get("source") == "personal_profile"
    if heart_rate is not None and heart_rate < thresholds.get("cardiac_low_hr", 40.0):
        _emit(
            alert_type="cardiac_anomaly",
            severity="critical",
            message=(
                f"{victim_id}: Low heart rate {heart_rate:.1f} bpm below personal "
                f"threshold {thresholds['cardiac_low_hr']:.1f}"
            ),
            ai_confidence=0.92,
            is_personal_alert=is_personal,
        )

    # ALERT 4 — Cardiac high HR (personal)
    if heart_rate is not None and heart_rate > thresholds.get("cardiac_high_hr", 150.0):
        _emit(
            alert_type="cardiac_anomaly",
            severity="critical",
            message=(
                f"{victim_id}: High heart rate {heart_rate:.1f} bpm above personal "
                f"threshold {thresholds['cardiac_high_hr']:.1f}"
            ),
            ai_confidence=0.92,
            is_personal_alert=is_personal,
        )

    # ALERT 5 — ML anomaly
    if (
        anomaly_result.get("is_anomaly") is True
        and anomaly_result.get("confidence", 0.0) > 0.6
        and anomaly_result.get("detector_status") == "active"
    ):
        _emit(
            alert_type="ml_anomaly",
            severity="warning",
            message=(
                f"{victim_id}: Anomalous vital pattern detected. "
                f"Anomaly score: {anomaly_result['anomaly_score']:.3f}. "
                f"Confidence: {anomaly_result['confidence']:.2f}"
            ),
            ai_confidence=anomaly_result["confidence"],
            is_personal_alert=True,
        )

    # ALERT 6 — Low SpO2
    spo2 = readings_dict.get("spo2")
    if spo2 is not None and spo2 < thresholds.get("low_spo2", 90.0):
        _emit(
            alert_type="low_spo2",
            severity="critical",
            message=(
                f"{victim_id}: Low oxygen saturation {spo2:.1f}% below threshold "
                f"{thresholds['low_spo2']:.1f}%"
            ),
            ai_confidence=0.90,
            is_personal_alert=True,
        )

    # ALERT 7 — Glucose
    glucose = readings_dict.get("glucose")
    if glucose is not None and thresholds.get("low_glucose") is not None and glucose < thresholds["low_glucose"]:
        _emit(
            alert_type="glucose_low",
            severity="critical",
            message=f"{victim_id}: Low glucose {glucose:.1f} mg/dL. Hypoglycemia risk.",
            ai_confidence=0.95,
            is_personal_alert=True,
        )
    if glucose is not None and thresholds.get("high_glucose") is not None and glucose > thresholds["high_glucose"]:
        _emit(
            alert_type="glucose_high",
            severity="warning",
            message=f"{victim_id}: High glucose {glucose:.1f} mg/dL. Hyperglycemia risk.",
            ai_confidence=0.88,
            is_personal_alert=True,
        )

    # ALERT 8 — Respiratory rate (personal thresholds)
    respiratory_rate = readings_dict.get("respiratory_rate")
    if respiratory_rate is not None and respiratory_rate < thresholds.get("low_rr", 8.0):
        _emit(
            alert_type="respiratory_anomaly",
            severity="critical",
            message=(
                f"{victim_id}: Low respiratory rate {respiratory_rate:.1f} br/min below personal "
                f"threshold {thresholds['low_rr']:.1f}"
            ),
            ai_confidence=0.90,
            is_personal_alert=is_personal,
        )
    if respiratory_rate is not None and respiratory_rate > thresholds.get("high_rr", 25.0):
        _emit(
            alert_type="respiratory_anomaly",
            severity="warning",
            message=(
                f"{victim_id}: High respiratory rate {respiratory_rate:.1f} br/min above personal "
                f"threshold {thresholds['high_rr']:.1f}"
            ),
            ai_confidence=0.90,
            is_personal_alert=is_personal,
        )

    return alerts
