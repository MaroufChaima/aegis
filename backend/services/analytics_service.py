"""
Analytics query functions for the AEGIS dashboard.

All queries target SQLite via SQLAlchemy ORM or raw text() SQL.
Timestamps are stored as ISO 8601 TEXT; SQLite's strftime() function is used
for time-bucketing since date_trunc() is a PostgreSQL-only function.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.alert import Alert
from models.device import Device
from models.telemetry import Telemetry
from models.uav import UAVPosition


def get_summary(db: Session) -> dict:
    """Build the full analytics summary dict for GET /api/analytics/summary.

    Queries the devices, alerts, telemetry, and uav_positions tables and
    aggregates the results into a single response dict.  All counts are
    computed with a single pass over each table to minimise query overhead.

    Args:
        db: SQLAlchemy session.

    Returns:
        Dict matching the API_FLOW.md summary response shape.
    """
    # --- Victim / device counts ---
    devices = db.query(Device).all()
    total_victims = len(devices)

    victims_by_priority: dict[str, int] = {"P1": 0, "P2": 0, "P3": 0}
    victims_by_status:   dict[str, int] = {"online": 0, "offline": 0, "sos": 0}
    hr_values:   list[float] = []
    temp_values: list[float] = []

    for dev in devices:
        pc = dev.priority_class or "P3"
        if pc in victims_by_priority:
            victims_by_priority[pc] += 1

        st = dev.status or "online"
        if st in victims_by_status:
            victims_by_status[st] += 1
        else:
            victims_by_status["online"] += 1

        if dev.heart_rate is not None:
            hr_values.append(dev.heart_rate)
        if dev.temperature is not None:
            temp_values.append(dev.temperature)

    avg_hr   = round(sum(hr_values)   / len(hr_values),   1) if hr_values   else 0.0
    avg_temp = round(sum(temp_values) / len(temp_values), 1) if temp_values else 0.0

    # --- Alert counts (last 60 minutes) ---
    one_hour_ago = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    recent_alerts = (
        db.query(Alert)
        .filter(Alert.timestamp >= one_hour_ago)
        .all()
    )
    total_alerts_last_hour = len(recent_alerts)

    alerts_by_type: dict[str, int] = {}
    for alert in recent_alerts:
        atype = alert.alert_type or "unknown"
        alerts_by_type[atype] = alerts_by_type.get(atype, 0) + 1

    # --- UAV stats ---
    uavs = db.query(UAVPosition).all()
    uavs_online = sum(1 for u in uavs if u.status in ("active", "returning"))

    # Network coverage: fraction of devices whose UAV relay is active
    active_relay_ids = {u.uav_id for u in uavs if u.status in ("active", "returning")}
    covered = sum(1 for d in devices if d.uav_relay_id in active_relay_ids)
    network_coverage_pct = round(covered / total_victims * 100) if total_victims else 0

    return {
        "total_victims":          total_victims,
        "victims_by_priority":    victims_by_priority,
        "victims_by_status":      victims_by_status,
        "total_alerts_last_hour": total_alerts_last_hour,
        "alerts_by_type":         alerts_by_type,
        "avg_heart_rate":         avg_hr,
        "avg_temperature":        avg_temp,
        "uavs_online":            uavs_online,
        "network_coverage_pct":   network_coverage_pct,
    }


def get_timeseries(db: Session) -> list[dict]:
    """Return alert counts binned into 5-minute intervals for the last 60 min.

    Uses SQLite's strftime() to extract year/month/day/hour and the
    integer-divided minute to form 5-minute bucket keys, then assembles the
    full list of expected bins (including zero-count gaps) so the chart always
    shows all 12 buckets.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of dicts with keys: timestamp (ISO 8601 bin start), count, critical_count.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # SQLite: bucket by floor(minute / 5) * 5
    sql = text("""
        SELECT
            strftime('%Y-%m-%dT%H', timestamp) || ':'
                || printf('%02d', (CAST(strftime('%M', timestamp) AS INTEGER) / 5) * 5)
                || ':00Z'                                           AS bin,
            COUNT(*)                                               AS total_count,
            SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS crit_count
        FROM alerts
        WHERE timestamp >= :cutoff
        GROUP BY bin
        ORDER BY bin
    """)

    rows = db.execute(sql, {"cutoff": cutoff}).fetchall()
    raw: dict[str, dict] = {
        row.bin: {"count": row.total_count, "critical_count": row.crit_count or 0}
        for row in rows
    }

    # Build all 12 expected bins regardless of whether data exists
    bins: list[dict] = []
    # Round now down to the current 5-minute boundary, then go back 11 buckets
    minute_floor = (now.minute // 5) * 5
    current_bin = now.replace(minute=minute_floor, second=0, microsecond=0)
    oldest_bin  = current_bin - timedelta(minutes=55)  # 12 bins total

    t = oldest_bin
    while t <= current_bin:
        key = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = raw.get(key, {"count": 0, "critical_count": 0})
        bins.append({
            "timestamp":     key,
            "count":         entry["count"],
            "critical_count": entry["critical_count"],
        })
        t += timedelta(minutes=5)

    return bins
