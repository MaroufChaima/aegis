"""
Database operations for the uav_positions table.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text

from models.uav import UAVPosition
from services.rescue_team_service import count_teams_near_region


def upsert_uav(db: Session, data: dict) -> UAVPosition:
    uav = db.query(UAVPosition).filter(UAVPosition.uav_id == data["uav_id"]).first()

    if uav is None:
        uav = UAVPosition(uav_id=data["uav_id"])
        db.add(uav)

    uav.timestamp         = data["timestamp"]
    uav.latitude          = data["latitude"]
    uav.longitude         = data["longitude"]
    uav.altitude          = data["altitude"]
    uav.battery           = data["battery"]
    uav.status            = data["status"]
    uav.coverage_radius   = data["coverage_radius"]
    uav.connected_devices = data["connected_devices"]
    if data.get("name"):
        uav.name = data["name"]
    if data.get("current_region"):
        uav.current_region = data["current_region"]
    if data.get("home_region"):
        uav.home_region = data["home_region"]

    db.commit()
    db.refresh(uav)
    return uav


def get_all_uavs(db: Session, region: str | None = None) -> list[UAVPosition]:
    q = db.query(UAVPosition)
    if region:
        q = q.filter(
            (UAVPosition.home_region == region) | (UAVPosition.current_region == region)
        )
    return q.order_by(UAVPosition.uav_id).all()


def get_all_uavs_enriched(db: Session, region: str | None = None) -> list[dict]:
    uavs = get_all_uavs(db, region)
    result = []
    for uav in uavs:
        victims = db.execute(
            text(
                """
                SELECT vcs.victim_id, v.name, vcs.gps_lat, vcs.gps_lon,
                       vcs.priority_class, vcs.severity_score
                FROM victim_current_state vcs
                JOIN victims v ON v.victim_id = vcs.victim_id
                WHERE vcs.uav_relay_id = :uid
                ORDER BY vcs.severity_score DESC
                """
            ),
            {"uid": uav.uav_id},
        ).fetchall()
        row = {
            "uav_id": uav.uav_id,
            "name": uav.name,
            "home_region": uav.home_region,
            "current_region": uav.current_region,
            "timestamp": uav.timestamp,
            "latitude": uav.latitude,
            "longitude": uav.longitude,
            "altitude": uav.altitude,
            "battery": uav.battery,
            "status": uav.status,
            "coverage_radius": uav.coverage_radius,
            "connected_devices": uav.connected_devices,
            "connected_users": [
                {
                    "victim_id": r[0], "name": r[1],
                    "gps_lat": r[2], "gps_lon": r[3],
                    "priority_class": r[4],
                }
                for r in victims
            ],
            "connected_victims": [
                {"victim_id": r[0], "name": r[1]} for r in victims
            ],
            "nearby_teams": count_teams_near_region(db, uav.current_region or uav.home_region),
        }
        result.append(row)
    return result
