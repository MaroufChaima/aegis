"""
Analytics query functions for the AEGIS dashboard.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.alert import Alert
from models.uav import UAVPosition
from services.victim_state_service import get_summary_stats


def _count_alerts(db: Session, cutoff: str, region: str | None = None) -> list:
    if region:
        rows = db.execute(
            text(
                """
                SELECT a.* FROM alerts a
                JOIN victims v ON a.victim_id = v.victim_id
                WHERE a.timestamp >= :cutoff
                  AND v.home_region = :region
                """
            ),
            {"cutoff": cutoff, "region": region},
        ).fetchall()
        return rows
    return db.query(Alert).filter(Alert.timestamp >= cutoff).all()


def get_summary(db: Session, scope: str = "global", region: str | None = None) -> dict:
    """Build analytics summary for global or regional scope."""
    if scope == "regional" and not region:
        scope = "global"

    wban_stats = get_summary_stats(db, region if scope == "regional" else None)
    total_victims = wban_stats["total_victims"]
    victims_by_priority = {"P1": 0, "P2": 0, "P3": 0, **wban_stats["victims_by_priority"]}
    victims_by_status = {"online": 0, "offline": 0, "critical": 0, "alert": 0, **wban_stats["victims_by_status"]}

    one_hour_ago = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    if scope == "regional" and region:
        recent_alert_rows = db.execute(
            text(
                """
                SELECT a.alert_type, a.severity FROM alerts a
                JOIN victims v ON a.victim_id = v.victim_id
                WHERE a.timestamp >= :cutoff AND v.home_region = :region
                """
            ),
            {"cutoff": one_hour_ago, "region": region},
        ).fetchall()
    else:
        recent_alerts = db.query(Alert).filter(Alert.timestamp >= one_hour_ago).all()
        recent_alert_rows = [(a.alert_type, a.severity) for a in recent_alerts]

    total_alerts_last_hour = len(recent_alert_rows)
    alerts_by_type: dict[str, int] = {}
    for atype, _ in recent_alert_rows:
        key = atype or "unknown"
        alerts_by_type[key] = alerts_by_type.get(key, 0) + 1

    uav_query = db.query(UAVPosition)
    if scope == "regional" and region:
        uav_query = uav_query.filter(
            (UAVPosition.home_region == region) | (UAVPosition.current_region == region)
        )
    uavs = uav_query.all()

    active_uavs = sum(1 for u in uavs if u.status == "active")
    standby_uavs = sum(1 for u in uavs if u.status == "standby")
    inactive_uavs = sum(1 for u in uavs if u.status in ("inactive", "offline"))

    relay_ids = {u.uav_id for u in uavs if u.status in ("active", "standby")}
    if scope == "regional" and region:
        relay_rows = db.execute(
            text(
                """
                SELECT vcs.uav_relay_id FROM victim_current_state vcs
                JOIN victims v ON vcs.victim_id = v.victim_id
                WHERE v.home_region = :region AND vcs.uav_relay_id IS NOT NULL
                """
            ),
            {"region": region},
        ).fetchall()
    else:
        relay_rows = db.execute(
            text("SELECT uav_relay_id FROM victim_current_state WHERE uav_relay_id IS NOT NULL")
        ).fetchall()
    covered = sum(1 for r in relay_rows if r[0] in relay_ids)
    network_coverage_pct = round(covered / total_victims * 100) if total_victims else 0

    # Rescue team counts (skeleton — full breakdown in R7/R8)
    if scope == "regional" and region:
        total_rescue_teams = db.execute(
            text("SELECT COUNT(*) FROM rescue_teams WHERE current_region = :region"),
            {"region": region},
        ).scalar() or 0
    else:
        total_rescue_teams = db.execute(
            text("SELECT COUNT(*) FROM rescue_teams")
        ).scalar() or 0

    teams_by_type, teams_by_status = _teams_by_type_status(
        db, region if scope == "regional" else None
    )

    base = {
        "scope": scope,
        "region": region,
        "total_victims": total_victims,
        "total_users": total_victims,
        "users_by_profile": _users_by_profile(db, region if scope == "regional" else None),
        "victims_by_priority": victims_by_priority,
        "victims_by_status": victims_by_status,
        "total_alerts_last_hour": total_alerts_last_hour,
        "active_alerts": total_alerts_last_hour,
        "alerts_by_type": alerts_by_type,
        "avg_heart_rate": wban_stats["avg_heart_rate"] or 0.0,
        "avg_temperature": wban_stats["avg_temperature"] or 0.0,
        "uavs_online": active_uavs,
        "uavs_standby": standby_uavs,
        "active_uavs": active_uavs,
        "inactive_uavs": inactive_uavs,
        "available_uavs": active_uavs + standby_uavs,
        "total_uavs": len(uavs) if uavs else (
            db.execute(text("SELECT COUNT(*) FROM uav_positions")).scalar() or 0
        ),
        "total_rescue_teams": total_rescue_teams,
        "rescue_teams_by_type": teams_by_type,
        "rescue_teams_by_status": teams_by_status,
        "network_coverage_pct": network_coverage_pct,
        "active_emergencies": wban_stats.get("active_emergencies", 0),
        "deaths": 0,
        "rescued_users": 0,
        "emergency_history": [],
        "regional_comparisons": [],
    }

    if scope == "global":
        base["regional_comparisons"] = _regional_comparisons(db)

    return base


def _users_by_profile(db: Session, region: str | None = None) -> dict:
    if region:
        rows = db.execute(
            text(
                "SELECT risk_category, COUNT(*) FROM victims WHERE home_region = :r GROUP BY risk_category"
            ),
            {"r": region},
        ).fetchall()
    else:
        rows = db.execute(
            text("SELECT risk_category, COUNT(*) FROM victims GROUP BY risk_category")
        ).fetchall()
    return {r[0] or "unknown": r[1] for r in rows}


def _teams_by_type_status(db: Session, region: str | None = None) -> tuple[dict, dict]:
    clause = "WHERE current_region = :r" if region else ""
    params = {"r": region} if region else {}
    type_rows = db.execute(
        text(f"SELECT team_type, COUNT(*) FROM rescue_teams {clause} GROUP BY team_type"),
        params,
    ).fetchall()
    status_rows = db.execute(
        text(f"SELECT status, COUNT(*) FROM rescue_teams {clause} GROUP BY status"),
        params,
    ).fetchall()
    return (
        {r[0] or "unknown": r[1] for r in type_rows},
        {r[0] or "unknown": r[1] for r in status_rows},
    )


def _regional_comparisons(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT v.home_region,
                   COUNT(DISTINCT v.victim_id) as user_count,
                   SUM(CASE WHEN vcs.emergency_status = 'victim' THEN 1 ELSE 0 END) as emergencies
            FROM victims v
            LEFT JOIN victim_current_state vcs ON v.victim_id = vcs.victim_id
            WHERE v.home_region IS NOT NULL
            GROUP BY v.home_region
            ORDER BY v.home_region
            """
        )
    ).fetchall()
    return [
        {"region": r[0], "user_count": r[1], "active_emergencies": r[2] or 0}
        for r in rows
    ]


def get_timeseries(db: Session) -> list[dict]:
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

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

    bins: list[dict] = []
    minute_floor = (now.minute // 5) * 5
    current_bin = now.replace(minute=minute_floor, second=0, microsecond=0)
    oldest_bin = current_bin - timedelta(minutes=55)

    t = oldest_bin
    while t <= current_bin:
        key = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = raw.get(key, {"count": 0, "critical_count": 0})
        bins.append({
            "timestamp": key,
            "count": entry["count"],
            "critical_count": entry["critical_count"],
        })
        t += timedelta(minutes=5)

    return bins
