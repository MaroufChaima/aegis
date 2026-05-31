"""
AI pipeline entry point for the AEGIS backend.

Exports a single function, ``run_ai_pipeline``, that chains the three AI
modules in the order documented in SIMPLIFIED_AI_MODULES.md:

    triage_scorer → anomaly_detector → alert_generator

Call this once per validated telemetry packet on the ingest path.
The db parameter is accepted for future use (e.g. querying device history
for seconds_since_movement) but the AI modules themselves remain pure —
no DB writes happen here.
"""

import logging
from sqlalchemy.orm import Session

from ai.triage_scorer import compute_severity_score, classify_priority
from ai.anomaly_detector import detector
from ai.alert_generator import decide_alerts

log = logging.getLogger(__name__)


def run_ai_pipeline(telemetry: dict, db: Session) -> dict:
    """Run the full AI pipeline for one telemetry packet.

    Chains three modules in order:

    1. **Triage scorer** — rule-based weighted scoring produces a
       ``severity_score`` (0–100) and ``priority_class`` (P1/P2/P3).
    2. **Anomaly detector** — IsolationForest predicts whether the
       packet's vital pattern is statistically unusual relative to the
       population of recent readings.
    3. **Alert generator** — evaluates trigger conditions against the
       triage and anomaly results; applies per-device cooldowns to
       suppress duplicate alerts.

    The ``db`` session is passed through so future phases can query
    device history (e.g. last-movement timestamp) without changing this
    function's signature.  The AI modules themselves perform no DB access.

    Args:
        telemetry: Validated, preprocessed telemetry dict from the ingest
                   pipeline.  Must contain at minimum: device_id, heart_rate,
                   temperature, sos_signal, movement, rssi, battery.
                   Optional: seconds_since_movement, seconds_since_last_seen.
        db:        SQLAlchemy session — available for history queries in
                   later phases; currently unused by the AI modules.

    Returns:
        Dict with the following keys:

        severity_score  (int)        0–100 from the rule-based scorer
        priority_class  (str)        "P1" | "P2" | "P3"
        is_anomaly      (bool)       True if IsolationForest flagged the packet
        anomaly_score   (float)      Raw IsolationForest score (more negative =
                                     more anomalous); 0.0 during cold start
        confidence      (float)      0.0–1.0 anomaly confidence
        alerts          (list[dict]) Zero or more alert dicts ready for
                                     alert_service.create_alert(); empty list
                                     if no thresholds were breached
    """
    # Step 1 — rule-based triage
    severity_score = compute_severity_score(telemetry)
    priority_class = classify_priority(severity_score)

    log.debug(
        "Triage: device=%s score=%d priority=%s",
        telemetry.get("device_id"), severity_score, priority_class,
    )

    # Step 2 — ML anomaly detection (singleton preserves model state)
    anomaly = detector.predict(telemetry)

    log.debug(
        "Anomaly: device=%s is_anomaly=%s confidence=%.2f",
        telemetry.get("device_id"), anomaly["is_anomaly"], anomaly["confidence"],
    )

    # Step 3 — alert generation
    ai_result = {
        "severity_score": severity_score,
        "priority_class": priority_class,
        "is_anomaly":     anomaly["is_anomaly"],
        "confidence":     anomaly["confidence"],
    }
    alerts = decide_alerts(telemetry, ai_result)

    return {
        "severity_score": severity_score,
        "priority_class": priority_class,
        "is_anomaly":     anomaly["is_anomaly"],
        "anomaly_score":  anomaly["anomaly_score"],
        "confidence":     anomaly["confidence"],
        "alerts":         alerts,
    }


__all__ = ["run_ai_pipeline"]
