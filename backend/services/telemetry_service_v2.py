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
    readings: dict,
) -> int:
    """Inserts one telemetry_readings row per sensor in the packet. Sensors with
    None values are stored with raw_value=NULL and raw_value_present=0. This
    preserves the distinction between a sensor that returned zero versus a sensor
    that failed to report. The imputation columns are left NULL here and filled by
    the imputation pipeline in phase M4."""

    rows_inserted = 0

    for sensor_type_id, value in readings.items():
        raw_value_present = 1 if value is not None else 0
        raw_value = value if value is not None else None

        db.execute(
            text(
                "INSERT INTO telemetry_readings "
                "(packet_id, victim_id, sensor_type_id, timestamp, raw_value, "
                "raw_value_present, imputed_value, imputation_method, "
                "imputation_confidence, is_anomaly_global, is_anomaly_personal, "
                "deviation_score, sensor_reliability) "
                "VALUES "
                "(:packet_id, :victim_id, :sensor_type_id, :timestamp, :raw_value, "
                ":raw_value_present, NULL, NULL, NULL, 0, 0, NULL, 1.0)"
            ),
            {
                "packet_id":         packet_id,
                "victim_id":         victim_id,
                "sensor_type_id":    sensor_type_id,
                "timestamp":         timestamp,
                "raw_value":         raw_value,
                "raw_value_present": raw_value_present,
            },
        )
        rows_inserted += 1

    db.commit()
    return rows_inserted


def upsert_victim_status(
    db: Session,
    victim_id: str,
    uav_relay_id: str,
    last_seen: str,
) -> None:
    """Updates the victim record with the latest UAV relay and last_seen timestamp.
    Called after every successful packet ingestion."""

    db.execute(
        text(
            "UPDATE victims SET uav_relay_id = :uav_relay_id "
            "WHERE victim_id = :victim_id"
        ),
        {"uav_relay_id": uav_relay_id, "victim_id": victim_id},
    )
    db.commit()
