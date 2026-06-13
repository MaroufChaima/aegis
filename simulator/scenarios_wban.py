"""
WBAN emergency scenarios for simulator_wban.py.
"""

import datetime
import random

import requests

from demo_config import REGIONS

UAV_UPDATE_URL = "http://localhost:8000/api/uavs/update"


def critical_vitals_wave(victims: list) -> list[str]:
    """Three victims spike to abnormal vitals (triggers automatic anomaly alerts)."""
    targets = random.sample(victims, min(3, len(victims)))
    for victim in targets:
        victim.profile._reading_overrides = {
            "heart_rate": 38.0,
            "temperature": 39.8,
            "spo2": 89.0,
            "respiratory_rate": 26.0,
        }
    return [v.victim_id for v in targets]


def mass_casualty(victims: list) -> list[str]:
    targets = random.sample(victims, min(5, len(victims)))
    for victim in targets:
        victim.profile._reading_overrides = {
            "heart_rate": 32.0,
            "temperature": 40.6,
            "spo2": 88.0,
            "respiratory_rate": 28.0,
            "blood_pressure_systolic": 85.0,
            "motion_activity": 0.0,
        }
    return [v.victim_id for v in targets]


def uav_failure(victims: list, uavs: list = None) -> str:
    relays = list({v.uav_relay_id for v in victims})
    target_uav = random.choice(relays)
    region = REGIONS.get("algiers")
    payload = {
        "uav_id": target_uav,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "latitude": region["center"][0],
        "longitude": region["center"][1],
        "altitude": 120.0,
        "battery": 0,
        "status": "offline",
        "coverage_radius": 500.0,
        "connected_devices": 0,
    }
    if uavs:
        for u in uavs:
            if u.uav_id == target_uav:
                u.status = "offline"
                u.battery = 0
    try:
        requests.post(UAV_UPDATE_URL, json=payload, timeout=4)
    except requests.RequestException as exc:
        print(f"[SCENARIO] uav_failure POST failed: {exc}")
    return target_uav


def gradual_deterioration(victims: list) -> str:
    target = random.choice(victims)
    target.profile.hr_baseline = max(target.profile.hr_baseline, 90.0)
    target.profile._deterioration_rate = 9
    target.profile._deterioration_ticks = 10
    return target.victim_id


def network_partition(victims: list) -> list[str]:
    relays = list({v.uav_relay_id for v in victims})
    target_relay = random.choice(relays)
    affected = []
    for victim in victims:
        if victim.uav_relay_id == target_relay:
            victim.profile._rssi_override = -125.0
            victim.profile._partition_ticks = 8
            affected.append(victim.victim_id)
    return affected


def apply_tick_effects(victims: list) -> None:
    for victim in victims:
        profile = victim.profile
        ticks = getattr(profile, "_deterioration_ticks", 0)
        if ticks > 0:
            rate = getattr(profile, "_deterioration_rate", 9)
            profile.hr_baseline = min(200.0, profile.hr_baseline + rate)
            profile._deterioration_ticks = ticks - 1
        pticks = getattr(profile, "_partition_ticks", 0)
        if pticks > 0:
            profile._partition_ticks = pticks - 1
            if profile._partition_ticks == 0:
                profile._rssi_override = None


SCENARIO_REGISTRY_WBAN = {
    "critical_vitals_wave": critical_vitals_wave,
    "mass_casualty": mass_casualty,
    "uav_failure": uav_failure,
    "gradual_deterioration": gradual_deterioration,
    "network_partition": network_partition,
}
