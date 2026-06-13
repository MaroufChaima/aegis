"""
WBAN UAV relay — 5 per region, standby default, active during emergency.
"""

import datetime
import random

import requests

from demo_config import REGIONS, uavs_for_region

UAV_UPDATE_URL = "http://localhost:8000/api/uavs/update"


class UAVWBAN:
    def __init__(self, uav_id: str, region_key: str, emergency_mode: bool = False):
        self.uav_id = uav_id
        self.name = uav_id
        self.region_key = region_key
        self.home_region = region_key
        region = REGIONS.get(region_key, REGIONS["algiers"])
        lat, lon = region["center"]
        self.latitude = lat + random.uniform(-0.004, 0.004)
        self.longitude = lon + random.uniform(-0.004, 0.004)
        self.altitude = random.uniform(100.0, 150.0)
        self.battery = random.randint(75, 100)
        self.status = "active" if emergency_mode else "standby"
        self.coverage_radius = 800.0
        self.connected_devices = 0

    def set_emergency_mode(self, active: bool):
        if self.status == "inactive":
            return
        self.status = "active" if active else "standby"

    def tick(self, connected_devices: int = 0):
        self.connected_devices = connected_devices
        self.latitude += random.uniform(-0.0003, 0.0003)
        self.longitude += random.uniform(-0.0003, 0.0003)
        self.altitude = max(80.0, self.altitude + random.uniform(-2.0, 2.0))
        if self.status == "active":
            self.battery = max(0, self.battery - random.randint(0, 1))

    def to_payload(self) -> dict:
        return {
            "uav_id": self.uav_id,
            "name": self.name,
            "home_region": self.home_region,
            "current_region": self.region_key,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "altitude": round(self.altitude, 1),
            "battery": int(self.battery),
            "status": self.status,
            "coverage_radius": self.coverage_radius,
            "connected_devices": self.connected_devices,
        }

    def post_update(self) -> bool:
        try:
            response = requests.post(UAV_UPDATE_URL, json=self.to_payload(), timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False


def create_uavs(region_key: str, emergency_mode: bool = False) -> list:
    return [UAVWBAN(uid, region_key, emergency_mode) for uid in uavs_for_region(region_key)]
