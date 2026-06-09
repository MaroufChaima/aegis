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
from models.uav import UAVPosition
from services.victim_state_service import get_summary_stats


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
    # --- Victim / device counts (from WBAN victim_current_state table) ---
    wban_stats = get_summary_stats(db)
    total_victims      = wban_stats["total_victims"]
    victims_by_priority = {"P1": 0, "P2": 0, "P3": 0, **wban_stats["victims_by_priority"]}
    victims_by_status   = {"online": 0, "offline": 0, "sos": 0, **wban_stats["victims_by_status"]}
    avg_hr   = wban_stats["avg_heart_rate"]   or 0.0
    avg_temp = wban_stats["avg_temperature"]  or 0.0

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
    uavs_online = wban_stats["uavs_online"]

    # Network coverage: victims whose relay UAV is currently active
    active_relay_ids = {u.uav_id for u in uavs if u.status in ("active", "returning")}
    relay_rows = db.execute(text(
        "SELECT uav_relay_id FROM victim_current_state WHERE uav_relay_id IS NOT NULL"
    )).fetchall()
    covered = sum(1 for r in relay_rows if r[0] in active_relay_ids)
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

    # SQLite: bucket by floor(minute / 5) * 5.
    #
    # Two SQLAlchemy / SQLite pitfalls avoided here:
    #  1. printf('%02d') is only available in SQLite >= 3.38.0 (Feb 2022).
    #     We use substr('00' || n, -2) instead, which works on all versions.
    #  2. SQLAlchemy's text() parser treats any :word token as a named bind
    #     parameter. Writing the colon as the SQL string literal ':' causes
    #     SQLAlchemy to parse ':00Z' as bind parameter "00Z" and crash with
    #     "A value is required for bind parameter '00Z'".
    #     We use char(58) (ASCII for ':') to produce the colon character
    #     without triggering the parameter parser.
    sql = text("""
        SELECT
            strftime('%Y-%m-%dT%H', timestamp)
                || char(58)
                || substr('00' || CAST((CAST(strftime('%M', timestamp) AS INTEGER) / 5) * 5 AS TEXT), -2)
                || char(58) || '00Z'                               AS bin,
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
