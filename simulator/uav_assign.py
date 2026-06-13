"""Local haversine UAV assignment for simulator ticks."""

import json
import math


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def assign_users_to_uavs(victims, uavs) -> None:
    for victim in victims:
        lat = victim.profile._gps_lat
        lon = victim.profile._gps_lon
        reachable = []
        for uav in uavs:
            if uav.status not in ("standby", "active"):
                continue
            d = haversine_m(lat, lon, uav.latitude, uav.longitude)
            if d <= uav.coverage_radius:
                reachable.append((d, uav.uav_id))
        reachable.sort(key=lambda x: x[0])
        primary = reachable[0][1] if reachable else None
        backups = [r[1] for r in reachable[1:3]]
        victim.uav_relay_id = primary
        victim.uav_backup_ids = backups
        victim.coordinator.uav_relay_id = primary
