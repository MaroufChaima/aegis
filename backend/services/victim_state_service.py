from sqlalchemy.orm import Session
from sqlalchemy import text


def upsert_victim_current_state(
    db: Session,
    victim_id: str,
    packet_id: int,
    packet_dict: dict,
    flat_readings: dict,
    ai_result: dict,
) -> None:
    """Upserts the current operational state for one victim after every successful packet ingestion. Uses INSERT OR REPLACE so that the first packet creates the row and every subsequent packet updates it. This table is the single source of truth for frontend victim state, map positions, and analytics aggregations. It replaces the legacy devices table."""

    sos = flat_readings.get('sos_signal', 0)

    state = {
        'victim_id': victim_id,
        'severity_score': ai_result.get('severity_score', 0),
        'priority_class': ai_result.get('priority_class', 'P3'),
        'is_anomaly': 1 if ai_result.get('is_anomaly', False) else 0,
        'heart_rate': flat_readings.get('heart_rate'),
        'temperature': flat_readings.get('temperature'),
        'spo2': flat_readings.get('spo2'),
        'blood_pressure_systolic': flat_readings.get('blood_pressure_systolic'),
        'blood_pressure_diastolic': flat_readings.get('blood_pressure_diastolic'),
        'glucose': flat_readings.get('glucose'),
        'respiratory_rate': flat_readings.get('respiratory_rate'),
        'battery': flat_readings.get('battery'),
        'gps_lat': flat_readings.get('gps_lat'),
        'gps_lon': flat_readings.get('gps_lon'),
        'rssi': packet_dict.get('rssi'),
        'uav_relay_id': packet_dict.get('uav_relay_id'),
        'sos_active': 1 if sos else 0,
        'packet_completeness': packet_dict.get('packet_completeness', 1.0),
        'last_packet_quality': packet_dict.get('packet_quality', 'good'),
        'status': 'sos' if sos else 'online',
        'last_seen': packet_dict.get('timestamp'),
        'last_packet_id': packet_id,
    }

    db.execute(
        text(
            """
            INSERT OR REPLACE INTO victim_current_state
            (victim_id, severity_score, priority_class, is_anomaly, heart_rate,
             temperature, spo2, blood_pressure_systolic, blood_pressure_diastolic,
             glucose, respiratory_rate, battery,
             gps_lat, gps_lon, rssi, uav_relay_id, sos_active, packet_completeness,
             last_packet_quality, status, last_seen, last_packet_id)
            VALUES
            (:victim_id, :severity_score, :priority_class, :is_anomaly, :heart_rate,
             :temperature, :spo2, :blood_pressure_systolic, :blood_pressure_diastolic,
             :glucose, :respiratory_rate, :battery,
             :gps_lat, :gps_lon, :rssi, :uav_relay_id, :sos_active, :packet_completeness,
             :last_packet_quality, :status, :last_seen, :last_packet_id)
            """
        ),
        state,
    )
    db.commit()


def get_all_victim_states(db: Session) -> list:
    """Returns all victim current states joined with victim identity data, sorted by severity_score descending so the highest priority victims appear first. Used by GET /api/victims for the dashboard victim table."""

    result = db.execute(
        text(
            """
            SELECT vcs.*, v.name, v.age, v.gender, v.risk_category,
                   v.medical_conditions, v.is_athlete, v.pregnancy_status
            FROM victim_current_state vcs
            JOIN victims v ON vcs.victim_id = v.victim_id
            ORDER BY vcs.severity_score DESC
            """
        )
    )
    rows = result.fetchall()
    if not rows:
        return []
    return [dict(row._mapping) for row in rows]


def get_victim_state(db: Session, victim_id: str) -> dict:
    """Returns the current state for one specific victim including identity fields. Returns None if the victim has not yet sent any packets."""

    result = db.execute(
        text(
            """
            SELECT vcs.*, v.name, v.age, v.gender, v.risk_category,
                   v.medical_conditions, v.is_athlete, v.pregnancy_status
            FROM victim_current_state vcs
            JOIN victims v ON vcs.victim_id = v.victim_id
            WHERE vcs.victim_id = :victim_id
            """
        ),
        {'victim_id': victim_id},
    )
    row = result.fetchone()
    if row is None:
        return None
    return dict(row._mapping)


def get_summary_stats(db: Session) -> dict:
    """Returns aggregated summary statistics for the analytics page. Reads from victim_current_state rather than the legacy devices table."""

    total = db.execute(
        text("SELECT COUNT(*) FROM victim_current_state")
    ).scalar()

    priority_rows = db.execute(
        text(
            "SELECT priority_class, COUNT(*) as count "
            "FROM victim_current_state GROUP BY priority_class"
        )
    ).fetchall()

    status_rows = db.execute(
        text(
            "SELECT status, COUNT(*) as count "
            "FROM victim_current_state GROUP BY status"
        )
    ).fetchall()

    avg_hr = db.execute(
        text(
            "SELECT AVG(heart_rate) FROM victim_current_state "
            "WHERE heart_rate IS NOT NULL"
        )
    ).scalar()

    avg_temp = db.execute(
        text(
            "SELECT AVG(temperature) FROM victim_current_state "
            "WHERE temperature IS NOT NULL"
        )
    ).scalar()

    uavs_online = db.execute(
        text("SELECT COUNT(*) FROM uav_positions WHERE status = 'active'")
    ).scalar()

    return {
        'total_victims': total or 0,
        'victims_by_priority': {row[0]: row[1] for row in priority_rows},
        'victims_by_status': {row[0]: row[1] for row in status_rows},
        'avg_heart_rate': round(float(avg_hr), 1) if avg_hr is not None else None,
        'avg_temperature': round(float(avg_temp), 1) if avg_temp is not None else None,
        'uavs_online': uavs_online or 0,
    }
