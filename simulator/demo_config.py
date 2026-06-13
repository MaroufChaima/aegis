"""Simulator demo config — mirrors backend/data/populations.py."""

from populations import (
    REGIONS, DEFAULT_REGION, USERS, PROFILES, SENSOR_ASSIGNMENTS,
    STANDARD_SENSORS, SENSOR_EXTRAS, PROFILE_TEMPLATES,
    _uav_id, _user_id,
)

def uavs_for_region(region_key: str):
    return [_uav_id(region_key, j) for j in range(5)]

def users_for_region(region_key: str):
    return [u for u in USERS if u["home_region"] == region_key]

def profile_for_user(user_id: str):
    for p in PROFILES:
        if p["victim_id"] == user_id:
            return p
    return PROFILE_TEMPLATES["healthy"]

def sensors_for_user(user_id: str):
    return [s["sensor_type_id"] for s in SENSOR_ASSIGNMENTS if s["victim_id"] == user_id]
