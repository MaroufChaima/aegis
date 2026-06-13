import json

from sqlalchemy.orm import Session
from sqlalchemy import text


def _derive_emergency_status(severity: int, priority_class: str) -> str:
    if priority_class == 'P1' or severity >= 40:
        return 'victim'
    return 'normal'


def _lookup_home_region(db: Session, victim_id: str) -> str | None:
    row = db.execute(
        text("SELECT home_region FROM victims WHERE victim_id = :id"),
        {"id": victim_id},
    ).fetchone()
    return row[0] if row else None


def upsert_victim_current_state(
    db: Session,
    victim_id: str,
    packet_id: int,
    packet_dict: dict,
    flat_readings: dict,
    ai_result: dict,
) -> None:
    is_anomaly = bool(ai_result.get('is_anomaly', False))
    severity = ai_result.get('severity_score', 0)
    if severity >= 70 or ai_result.get('priority_class') == 'P1':
        status = 'critical'
    elif is_anomaly:
        status = 'alert'
    else:
        status = 'online'

    emergency_status = _derive_emergency_status(severity, ai_result.get('priority_class', 'P3'))
    current_region = packet_dict.get('current_region') or _lookup_home_region(db, victim_id)
    altitude_m = flat_readings.get('altitude_m')
    if altitude_m is None:
        altitude_m = flat_readings.get('gps_alt')

    backup_ids = packet_dict.get('uav_backup_ids')
    if isinstance(backup_ids, list):
        backup_json = json.dumps(backup_ids)
    elif isinstance(backup_ids, str):
        backup_json = backup_ids
    else:
        backup_json = '[]'

    state = {
        'victim_id': victim_id,
        'severity_score': severity,
        'priority_class': ai_result.get('priority_class', 'P3'),
        'is_anomaly': 1 if is_anomaly else 0,
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
        'altitude_m': altitude_m,
        'rssi': packet_dict.get('rssi'),
        'uav_relay_id': packet_dict.get('uav_relay_id'),
        'uav_backup_ids': backup_json,
        'current_region': current_region,
        'emergency_status': emergency_status,
        'packet_completeness': packet_dict.get('packet_completeness', 1.0),
        'last_packet_quality': packet_dict.get('packet_quality', 'good'),
        'status': status,
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
             gps_lat, gps_lon, altitude_m, rssi, uav_relay_id, uav_backup_ids,
             current_region, emergency_status, packet_completeness,
             last_packet_quality, status, last_seen, last_packet_id)
            VALUES
            (:victim_id, :severity_score, :priority_class, :is_anomaly, :heart_rate,
             :temperature, :spo2, :blood_pressure_systolic, :blood_pressure_diastolic,
             :glucose, :respiratory_rate, :battery,
             :gps_lat, :gps_lon, :altitude_m, :rssi, :uav_relay_id, :uav_backup_ids,
             :current_region, :emergency_status, :packet_completeness,
             :last_packet_quality, :status, :last_seen, :last_packet_id)
            """
        ),
        state,
    )
    db.commit()


def get_all_victim_states(db: Session, region: str | None = None) -> list:
    query = """
        SELECT vcs.*, v.name, v.age, v.gender, v.risk_category,
               v.medical_conditions, v.is_athlete, v.pregnancy_status,
               v.height_cm, v.weight_kg, v.home_region
        FROM victim_current_state vcs
        JOIN victims v ON vcs.victim_id = v.victim_id
    """
    params = {}
    if region:
        query += " WHERE v.home_region = :region OR vcs.current_region = :region"
        params["region"] = region
    query += " ORDER BY vcs.severity_score DESC"

    result = db.execute(text(query), params)
    rows = result.fetchall()
    if not rows:
        return []
    return [dict(row._mapping) for row in rows]


def get_victim_state(db: Session, victim_id: str) -> dict:
    result = db.execute(
        text(
            """
            SELECT vcs.*, v.name, v.age, v.gender, v.risk_category,
                   v.medical_conditions, v.is_athlete, v.pregnancy_status,
                   v.height_cm, v.weight_kg, v.home_region
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


def get_summary_stats(db: Session, region: str | None = None) -> dict:
    if region:
        total = db.execute(
            text(
                """
                SELECT COUNT(*) FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE v.home_region = :region OR vcs.current_region = :region
                """
            ),
            {"region": region},
        ).scalar()

        priority_rows = db.execute(
            text(
                """
                SELECT vcs.priority_class, COUNT(*) as count
                FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE v.home_region = :region OR vcs.current_region = :region
                GROUP BY vcs.priority_class
                """
            ),
            {"region": region},
        ).fetchall()

        status_rows = db.execute(
            text(
                """
                SELECT vcs.status, COUNT(*) as count
                FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE v.home_region = :region OR vcs.current_region = :region
                GROUP BY vcs.status
                """
            ),
            {"region": region},
        ).fetchall()

        avg_hr = db.execute(
            text(
                """
                SELECT AVG(vcs.heart_rate) FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE (v.home_region = :region OR vcs.current_region = :region)
                  AND vcs.heart_rate IS NOT NULL
                """
            ),
            {"region": region},
        ).scalar()

        avg_temp = db.execute(
            text(
                """
                SELECT AVG(vcs.temperature) FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE (v.home_region = :region OR vcs.current_region = :region)
                  AND vcs.temperature IS NOT NULL
                """
            ),
            {"region": region},
        ).scalar()

        active_emergencies = db.execute(
            text(
                """
                SELECT COUNT(*) FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE (v.home_region = :region OR vcs.current_region = :region)
                  AND vcs.emergency_status = 'victim'
                """
            ),
            {"region": region},
        ).scalar()

        uavs_active = db.execute(
            text(
                """
                SELECT COUNT(*) FROM uav_positions
                WHERE status = 'active'
                  AND (home_region = :region OR current_region = :region)
                """
            ),
            {"region": region},
        ).scalar()

        uavs_standby = db.execute(
            text(
                """
                SELECT COUNT(*) FROM uav_positions
                WHERE status = 'standby'
                  AND (home_region = :region OR current_region = :region)
                """
            ),
            {"region": region},
        ).scalar()
    else:
        total = db.execute(text("SELECT COUNT(*) FROM victim_current_state")).scalar()

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

        active_emergencies = db.execute(
            text(
                "SELECT COUNT(*) FROM victim_current_state "
                "WHERE emergency_status = 'victim'"
            )
        ).scalar()

        uavs_active = db.execute(
            text("SELECT COUNT(*) FROM uav_positions WHERE status = 'active'")
        ).scalar()

        uavs_standby = db.execute(
            text("SELECT COUNT(*) FROM uav_positions WHERE status = 'standby'")
        ).scalar()

    return {
        'total_victims': total or 0,
        'victims_by_priority': {row[0]: row[1] for row in priority_rows},
        'victims_by_status': {row[0]: row[1] for row in status_rows},
        'avg_heart_rate': round(float(avg_hr), 1) if avg_hr is not None else None,
        'avg_temperature': round(float(avg_temp), 1) if avg_temp is not None else None,
        'uavs_online': uavs_active or 0,
        'uavs_standby': uavs_standby or 0,
        'active_emergencies': active_emergencies or 0,
    }
