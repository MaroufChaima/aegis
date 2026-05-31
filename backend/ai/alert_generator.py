"""
Alert generator for the AEGIS AI pipeline.

Decides which alerts to create for a given telemetry + AI result pair.
Applies a per-device, per-alert-type cooldown to prevent alert storms
during prolonged emergencies.

Design constraints:
- No database access — callers are responsible for persisting returned dicts.
- Module-level cooldown dict is the only shared state; it resets on restart,
  which is acceptable for a prototype (alerts are regenerated naturally on
  the next out-of-cooldown window).
- All trigger thresholds match MVP_FEATURES.md exactly.
"""

import time
import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cooldown tracker
# ---------------------------------------------------------------------------

COOLDOWN_SECONDS = 300  # 5 minutes — same device+type within this window is skipped

# key: "device_id:alert_type" → Unix timestamp of last alert emission
_last_alert_time: dict[str, float] = {}


def _on_cooldown(device_id: str, alert_type: str) -> bool:
    """Return True if this device+type combination is within the cooldown window.

    Args:
        device_id:  Unique device identifier, e.g. "WB-007".
        alert_type: Alert category string, e.g. "cardiac_anomaly".

    Returns:
        True if fewer than COOLDOWN_SECONDS have elapsed since the last
        alert of this type for this device; False otherwise.
    """
    key = f"{device_id}:{alert_type}"
    last = _last_alert_time.get(key)
    return last is not None and (time.time() - last) < COOLDOWN_SECONDS


def _record_alert(device_id: str, alert_type: str) -> None:
    """Mark this device+type as having just fired an alert.

    Args:
        device_id:  Unique device identifier.
        alert_type: Alert category string.
    """
    _last_alert_time[f"{device_id}:{alert_type}"] = time.time()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def decide_alerts(telemetry: dict, ai_result: dict) -> list[dict]:
    """Determine which alerts to generate for one telemetry + AI result pair.

    Evaluates five trigger conditions in priority order. Each condition that
    fires — and is not suppressed by the cooldown — appends one alert dict
    to the returned list. An empty list means no new alerts should be created.

    Trigger conditions and thresholds (source: MVP_FEATURES.md):

    +--------------------+-----------------------------------+-----------+
    | alert_type         | Condition                         | Severity  |
    +====================+===================================+===========+
    | p1_classification  | priority_class == "P1"            | critical  |
    | sos_signal         | sos_signal is truthy              | critical  |
    | cardiac_anomaly    | heart_rate < 40 OR > 150 bpm      | critical  |
    | no_movement        | seconds_since_movement > 600 s    | warning   |
    | ml_anomaly         | is_anomaly=True AND confidence>0.6| warning   |
    +--------------------+-----------------------------------+-----------+

    Cooldown: any device+type pair that fired within the last 300 seconds
    is silently skipped. This prevents alert flooding during prolonged
    emergencies while still re-alerting if the condition persists after the
    cooldown window expires.

    Args:
        telemetry: Dict produced by the ingest pipeline. Expected keys:
                       device_id (str), heart_rate (int), sos_signal (bool|int),
                       seconds_since_movement (int, optional — defaults to 0).
        ai_result: Dict returned by the AI pipeline. Expected keys:
                       severity_score (int), priority_class (str),
                       is_anomaly (bool), confidence (float 0–1).

    Returns:
        List of alert dicts, each containing:
            device_id (str), alert_type (str), severity (str),
            message (str), ai_confidence (float).
        The list may be empty. Callers must persist each dict via the
        alert service — this function has no side effects beyond the
        module-level cooldown tracker.
    """
    alerts: list[dict] = []
    device_id = telemetry["device_id"]
    hr        = telemetry.get("heart_rate", 70)
    sos       = bool(telemetry.get("sos_signal", False))
    secs_idle = int(telemetry.get("seconds_since_movement", 0))

    priority   = ai_result.get("priority_class", "P3")
    score      = ai_result.get("severity_score", 0)
    is_anomaly = bool(ai_result.get("is_anomaly", False))
    confidence = float(ai_result.get("confidence", 0.0))

    def _emit(alert_type: str, severity: str, message: str, conf: float = 1.0) -> None:
        """Append an alert if not on cooldown, then record the emission time."""
        if _on_cooldown(device_id, alert_type):
            log.debug(
                "Alert suppressed (cooldown): device=%s type=%s",
                device_id, alert_type,
            )
            return
        alerts.append({
            "device_id":    device_id,
            "alert_type":   alert_type,
            "severity":     severity,
            "message":      message,
            "ai_confidence": conf,
        })
        _record_alert(device_id, alert_type)
        log.info("Alert generated: device=%s type=%s severity=%s", device_id, alert_type, severity)

    # --- P1 classification ---
    if priority == "P1":
        _emit(
            "p1_classification",
            "critical",
            f"{device_id}: Classified as Priority 1 (Critical). "
            f"Severity score: {score}/100.",
        )

    # --- SOS signal ---
    if sos:
        _emit(
            "sos_signal",
            "critical",
            f"{device_id}: SOS signal activated. Immediate response required.",
        )

    # --- Cardiac anomaly ---
    if hr < 40:
        _emit(
            "cardiac_anomaly",
            "critical",
            f"{device_id}: Critically low heart rate detected ({hr} bpm). "
            "Possible cardiac arrest.",
        )
    elif hr > 150:
        _emit(
            "cardiac_anomaly",
            "critical",
            f"{device_id}: Dangerously high heart rate detected ({hr} bpm). "
            "Possible shock or severe tachycardia.",
        )

    # --- Prolonged inactivity ---
    if secs_idle > 600:
        minutes = secs_idle // 60
        _emit(
            "no_movement",
            "warning",
            f"{device_id}: No movement detected for {minutes} minute(s). "
            "Victim may be unconscious or incapacitated.",
        )

    # --- ML anomaly (only above confidence threshold) ---
    if is_anomaly and confidence > 0.6:
        _emit(
            "ml_anomaly",
            "warning",
            f"{device_id}: Unusual vital pattern detected by AI system. "
            f"Confidence: {int(confidence * 100)}%. Manual verification recommended.",
            conf=confidence,
        )

    return alerts
