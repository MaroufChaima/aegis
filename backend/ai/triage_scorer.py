"""
Rule-based triage scorer for the AEGIS AI pipeline.

Pure functions only — no database access, no side effects, no imports
beyond the standard library. Safe to call from any context and trivial
to unit-test in isolation.

Scoring weights and priority thresholds match MVP_FEATURES.md exactly.
Each condition's clinical rationale is documented alongside its weight.
"""


def compute_severity_score(telemetry: dict) -> int:
    """Compute a severity score (0–100) from a single telemetry reading.

    Each condition adds a fixed number of points. Points accumulate and
    are clamped to 100. This additive, transparent approach lets operators
    understand exactly which signals drove the score — important for a
    safety-critical system where black-box decisions are unacceptable.

    The function reads the following keys from ``telemetry``:

    Required:
        heart_rate (int)       — beats per minute
        temperature (float)    — degrees Celsius
        sos_signal (bool|int)  — explicit distress call from the device
        movement (bool|int)    — whether the device detected motion
        rssi (int)             — received signal strength in dBm
        battery (int)          — remaining charge 0–100%

    Optional (default to 0 if absent — no time-based penalty applied):
        seconds_since_movement (int)   — elapsed seconds since last movement event;
                                         populated by the ingest pipeline from the
                                         device's last_seen history
        seconds_since_last_seen (int)  — elapsed seconds since the last successful
                                         packet from this device

    Scoring weights (source: MVP_FEATURES.md):
        +50  SOS signal active           — explicit distress call
        +40  Heart rate < 40 bpm         — severe bradycardia / cardiac arrest risk
        +20  Heart rate > 150 bpm        — severe tachycardia / shock
        +15  Temperature > 39 °C         — high-grade fever / systemic infection
        +25  Temperature < 35 °C         — hypothermia risk
        +25  No movement ≥ 600 s         — victim likely incapacitated or unconscious
        +10  No movement ≥ 300 s         — early inactivity warning (mutually exclusive
                                           with the 600 s rule — only the higher applies)
        +30  Offline ≥ 300 s (5 min)     — connectivity loss, victim location unknown
        +10  RSSI < −100 dBm             — poor signal, data reliability reduced
        +5   Battery < 10%               — device may go offline soon

    Args:
        telemetry: Dict produced by the ingest pipeline.  Any key not present
                   defaults to a value that does not trigger that condition.

    Returns:
        Integer in the range [0, 100]. Higher means more critical.
    """
    score = 0

    # --- SOS ---
    if telemetry.get("sos_signal"):
        score += 50

    # --- Heart rate ---
    hr = telemetry.get("heart_rate", 70)
    if hr < 40:
        score += 40        # severe bradycardia
    elif hr > 150:
        score += 20        # severe tachycardia

    # --- Temperature ---
    temp = telemetry.get("temperature", 37.0)
    if temp > 39.0:
        score += 15        # high-grade fever
    if temp < 35.0:
        score += 25        # hypothermia (not elif — both can be true in corrupted data)

    # --- Movement inactivity ---
    secs_no_move = telemetry.get("seconds_since_movement", 0)
    if secs_no_move >= 600:
        score += 25        # likely unconscious / incapacitated
    elif secs_no_move >= 300:
        score += 10        # early inactivity warning

    # --- Connectivity loss ---
    secs_offline = telemetry.get("seconds_since_last_seen", 0)
    if secs_offline >= 300:
        score += 30        # 5+ minutes without a packet

    # --- Signal quality ---
    if telemetry.get("rssi", 0) < -100:
        score += 10        # poor LoRaWAN link

    # --- Battery ---
    if telemetry.get("battery", 100) < 10:
        score += 5         # device close to dying

    return min(score, 100)


def classify_priority(score: int) -> str:
    """Map a numeric severity score to a priority class.

    Thresholds are defined in MVP_FEATURES.md and are consistent with
    emergency triage frameworks adapted for IoT-based remote monitoring:

        P1 (Critical) — score ≥ 70 — immediate intervention required
        P2 (Urgent)   — score 40–69 — elevated risk, close monitoring
        P3 (Stable)   — score < 40  — within acceptable parameters

    These thresholds were chosen so that a single maximum-weight trigger
    (SOS: +50) alone does not automatically escalate to P1, requiring at
    least one additional physiological anomaly — reducing false P1 alerts
    during accidental SOS activations.

    Args:
        score: Integer in [0, 100] as returned by compute_severity_score().

    Returns:
        "P1", "P2", or "P3".
    """
    if score >= 70:
        return "P1"
    if score >= 40:
        return "P2"
    return "P3"
