"""Haversine UAV assignment — nearest UAV within coverage radius."""

import json
import math

from sqlalchemy import text
from sqlalchemy.orm import Session


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def assign_uavs_for_region(db: Session, region: str, emergency_mode: bool = False) -> dict:
    """Assign primary + backup UAVs for all users with GPS in a region."""
    uav_status_filter = ("standby", "active") if not emergency_mode else ("active", "standby")
    uavs = db.execute(
        text("""
            SELECT uav_id, latitude, longitude, coverage_radius, status
            FROM uav_positions
            WHERE (home_region = :r OR current_region = :r)
              AND latitude IS NOT NULL AND longitude IS NOT NULL
              AND status IN ('standby', 'active', 'inactive')
        """),
        {"r": region},
    ).fetchall()

    users = db.execute(
        text("""
            SELECT vcs.victim_id, vcs.gps_lat, vcs.gps_lon
            FROM victim_current_state vcs
            JOIN victims v ON v.victim_id = vcs.victim_id
            WHERE v.home_region = :r AND vcs.gps_lat IS NOT NULL AND vcs.gps_lon IS NOT NULL
        """),
        {"r": region},
    ).fetchall()

    assignments = {}
    for user in users:
        uid, lat, lon = user[0], user[1], user[2]
        reachable = []
        for uav in uavs:
            if uav[3] is None:
                continue
            dist = _haversine_m(lat, lon, uav[1], uav[2])
            if dist <= (uav[3] or 800):
                reachable.append((dist, uav[0]))
        reachable.sort(key=lambda x: x[0])
        primary = reachable[0][1] if reachable else None
        backups = [r[1] for r in reachable[1:3]]
        assignments[uid] = {"primary": primary, "backups": backups}
        if primary:
            db.execute(
                text("""
                    UPDATE victim_current_state
                    SET uav_relay_id = :primary, uav_backup_ids = :backups
                    WHERE victim_id = :uid
                """),
                {"primary": primary, "backups": json.dumps(backups), "uid": uid},
            )
    db.commit()
    return assignments


def assign_uavs_for_user_latlon(
    user_id: str, lat: float, lon: float, uavs: list, coverage_default: float = 800.0
) -> tuple[str | None, list]:
    """Simulator-side assignment from in-memory UAV list."""
    reachable = []
    for uav in uavs:
        dist = _haversine_m(lat, lon, uav.latitude, uav.longitude)
        radius = uav.coverage_radius or coverage_default
        if dist <= radius and uav.status in ("standby", "active"):
            reachable.append((dist, uav.uav_id))
    reachable.sort(key=lambda x: x[0])
    primary = reachable[0][1] if reachable else None
    backups = [r[1] for r in reachable[1:3]]
    return primary, backups
