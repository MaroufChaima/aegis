"""
WBAN emergency scenarios for simulator_wban.py.

Each handler mutates VictimWBAN instances in memory. Changes flow through the
next coordinator packet posted to /api/v2/ingest.
"""

import datetime
import random

import requests

UAV_UPDATE_URL = "http://localhost:8000/api/uavs/update"


def sos_wave(victims: list) -> list[str]:
    """Activate SOS on three random victims."""
    targets = random.sample(victims, min(3, len(victims)))
    for victim in targets:
        victim.sos_active = True
    return [v.victim_id for v in targets]


def mass_casualty(victims: list) -> list[str]:
    """Drop five victims to critical vitals via reading overrides."""
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


def uav_failure(victims: list) -> str:
    """Take one UAV offline via the backend update endpoint."""
    relays = list({v.uav_relay_id for v in victims})
    target_uav = random.choice(relays)
    payload = {
        "uav_id": target_uav,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "latitude": 36.7321,
        "longitude": 3.0841,
        "altitude": 120.0,
        "battery": 0,
        "status": "offline",
        "coverage_radius": 500.0,
        "connected_devices": 0,
    }
    try:
        requests.post(UAV_UPDATE_URL, json=payload, timeout=4)
    except requests.RequestException as exc:
        print(f"[SCENARIO] uav_failure POST failed: {exc}")
    return target_uav


def gradual_deterioration(victims: list) -> str:
    """Escalate one victim's HR baseline over subsequent ticks."""
    target = random.choice(victims)
    target.profile.hr_baseline = max(target.profile.hr_baseline, 90.0)
    target.profile._deterioration_rate = 9
    target.profile._deterioration_ticks = 10
    return target.victim_id


def network_partition(victims: list) -> list[str]:
    """Degrade connectivity for all victims on one UAV relay."""
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
    """Advance multi-tick scenario effects."""
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
    "sos_wave": sos_wave,
    "mass_casualty": mass_casualty,
    "uav_failure": uav_failure,
    "gradual_deterioration": gradual_deterioration,
    "network_partition": network_partition,
}
