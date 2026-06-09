"""
Database write functions for the WBAN coordinator packet ingest pipeline.
All functions use parameterized queries exclusively — no string formatting
is used to build SQL.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime


def check_duplicate_packet(db: Session, victim_id: str, timestamp: str) -> bool:
    """Returns True if a packet with this exact victim_id and timestamp already
    exists in the database. Used to prevent duplicate processing when the simulator
    retries a failed POST."""

    result = db.execute(
        text(
            "SELECT COUNT(*) FROM coordinator_packets "
            "WHERE victim_id = :victim_id AND timestamp = :timestamp"
        ),
        {"victim_id": victim_id, "timestamp": timestamp},
    )
    return result.scalar() > 0


def insert_coordinator_packet(db: Session, packet_dict: dict) -> int:
    """Inserts one coordinator packet record and returns the generated packet_id.
    The packet_id is needed immediately to create the associated telemetry_readings
    rows."""

    db.execute(
        text(
            "INSERT INTO coordinator_packets "
            "(victim_id, coordinator_id, uav_relay_id, timestamp, received_at, "
            "sensor_count_expected, sensor_count_received, packet_completeness, "
            "rssi, snr, packet_quality, is_duplicate, notes) "
            "VALUES "
            "(:victim_id, :coordinator_id, :uav_relay_id, :timestamp, :received_at, "
            ":sensor_count_expected, :sensor_count_received, :packet_completeness, "
            ":rssi, :snr, :packet_quality, 0, NULL)"
        ),
        {
            "victim_id":             packet_dict["victim_id"],
            "coordinator_id":        packet_dict["coordinator_id"],
            "uav_relay_id":          packet_dict.get("uav_relay_id"),
            "timestamp":             packet_dict["timestamp"],
            "received_at":           packet_dict.get("received_at"),
            "sensor_count_expected": packet_dict["sensor_count_expected"],
            "sensor_count_received": packet_dict["sensor_count_received"],
            "packet_completeness":   packet_dict["packet_completeness"],
            "rssi":                  packet_dict.get("rssi"),
            "snr":                   packet_dict.get("snr"),
            "packet_quality":        packet_dict.get("packet_quality"),
        },
    )

    packet_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
    db.commit()
    return int(packet_id)


def insert_telemetry_readings(
    db: Session,
    packet_id: int,
    victim_id: str,
    timestamp: str,
    enriched_readings: dict,
) -> int:
    """Inserts one telemetry_readings row per sensor in the packet. Each row stores
    both the raw value (if the sensor reported) and the imputed value with its method
    and confidence score (set by the imputation and confidence scoring pipeline).
    Sensors with no raw value have raw_value=NULL and raw_value_present=0."""

    rows_inserted = 0

    for sensor_type_id, reading_dict in enriched_readings.items():
        raw_value            = reading_dict.get("raw_value")
        raw_value_present    = 1 if raw_value is not None else 0
        imputed_value        = reading_dict.get("imputed_value")
        imputation_method    = reading_dict.get("imputation_method")
        imputation_confidence = reading_dict.get("imputation_confidence")

        db.execute(
            text(
                "INSERT INTO telemetry_readings "
                "(packet_id, victim_id, sensor_type_id, timestamp, raw_value, "
                "raw_value_present, imputed_value, imputation_method, "
                "imputation_confidence, is_anomaly_global, is_anomaly_personal, "
                "deviation_score, sensor_reliability) "
                "VALUES "
                "(:packet_id, :victim_id, :sensor_type_id, :timestamp, :raw_value, "
                ":raw_value_present, :imputed_value, :imputation_method, "
                ":imputation_confidence, 0, 0, NULL, 1.0)"
            ),
            {
                "packet_id":             packet_id,
                "victim_id":             victim_id,
                "sensor_type_id":        sensor_type_id,
                "timestamp":             timestamp,
                "raw_value":             raw_value,
                "raw_value_present":     raw_value_present,
                "imputed_value":         imputed_value,
                "imputation_method":     imputation_method,
                "imputation_confidence": imputation_confidence,
            },
        )
        rows_inserted += 1

    db.commit()
    return rows_inserted


def update_readings_with_ai_results(db: Session, packet_id: int, ai_result: dict) -> None:
    """Updates the is_anomaly_global and is_anomaly_personal flags on telemetry_readings
    rows after the AI pipeline has run. Called after insert_telemetry_readings so that
    the rows exist before we try to update them. Separate from the insert to keep the
    AI pipeline result handling isolated."""

    global_flags   = ai_result.get("global_anomaly_flags", {})
    personal_flags = ai_result.get("personal_anomaly_flags", {})

    all_sensors = set(global_flags.keys()) | set(personal_flags.keys())

    for sensor_type_id in all_sensors:
        global_flag   = 1 if global_flags.get(sensor_type_id) else 0
        personal_flag = 1 if personal_flags.get(sensor_type_id) else 0

        db.execute(
            text(
                "UPDATE telemetry_readings "
                "SET is_anomaly_global = :global_flag, is_anomaly_personal = :personal_flag "
                "WHERE packet_id = :packet_id AND sensor_type_id = :sensor_type_id"
            ),
            {
                "global_flag":    global_flag,
                "personal_flag":  personal_flag,
                "packet_id":      packet_id,
                "sensor_type_id": sensor_type_id,
            },
        )

    db.commit()


def upsert_victim_status(
    db: Session,
    victim_id: str,
    uav_relay_id: str,
    last_seen: str,
) -> None:
    """No-op in the WBAN architecture. UAV relay info is stored per-packet in
    coordinator_packets.uav_relay_id. The victims table does not carry a mutable
    last_seen or uav_relay_id column — those fields live on the legacy devices table.
    Function signature kept for call-site compatibility."""
    pass
