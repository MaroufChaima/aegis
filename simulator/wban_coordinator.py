"""
Simulates the WBAN coordinator node that aggregates sensor readings from all
wearables attached to one victim. The coordinator transmits a single packet
containing all available readings. Missing sensors are represented as None values
in the readings dict rather than being omitted — this distinction is critical for
the imputation pipeline.
"""

import datetime
import random

from wearable_sensor import WearableSensor, SensorStatus
from physiological_profile import PhysiologicalProfile


class WBANCoordinator:
    """Simulates the WBAN coordinator node that aggregates sensor readings from all
    wearables attached to one victim. The coordinator transmits a single packet
    containing all available readings. Missing sensors are represented as None values
    in the readings dict rather than being omitted — this distinction is critical for
    the imputation pipeline."""

    def __init__(
        self,
        victim_id: str,
        coordinator_id: str,
        sensors: list,
        profile: PhysiologicalProfile,
        uav_relay_id: str,
    ):
        self.victim_id      = victim_id
        self.coordinator_id = coordinator_id
        self.sensors        = sensors
        self.profile        = profile
        self.uav_relay_id   = uav_relay_id

    def tick(self):
        for sensor in self.sensors:
            sensor.tick()
        for sensor in self.sensors:
            if sensor.status is SensorStatus.DISCONNECTED:
                sensor.attempt_reconnect()

    def collect_readings(self) -> dict:
        readings = {}
        for sensor in self.sensors:
            if sensor.read():
                readings[sensor.sensor_type_id] = self.profile.generate_reading(
                    sensor.sensor_type_id
                )
            else:
                readings[sensor.sensor_type_id] = None
        return readings

    def build_packet(self, sos_active: bool = False) -> dict:
        readings = self.collect_readings()

        if sos_active:
            readings["sos_signal"] = 1.0

        sensor_count_expected = len(self.sensors)
        sensor_count_received = sum(1 for v in readings.values() if v is not None)

        if sensor_count_expected > 0:
            packet_completeness = round(
                sensor_count_received / sensor_count_expected, 3
            )
        else:
            packet_completeness = 0.0

        rssi = readings.get("rssi")
        if rssi is None:
            rssi = -85.0

        snr = round(random.uniform(5.0, 12.0), 1)

        if packet_completeness >= 0.8:
            packet_quality = "good"
        elif packet_completeness >= 0.5:
            packet_quality = "degraded"
        else:
            packet_quality = "poor"

        sensor_statuses = {
            sensor.sensor_type_id: sensor.status_string for sensor in self.sensors
        }

        sensor_batteries = {
            sensor.sensor_type_id: round(sensor.battery, 1) for sensor in self.sensors
        }

        return {
            "victim_id":             self.victim_id,
            "coordinator_id":        self.coordinator_id,
            "uav_relay_id":          self.uav_relay_id,
            "timestamp":             datetime.datetime.utcnow().isoformat() + "Z",
            "sensor_count_expected": sensor_count_expected,
            "sensor_count_received": sensor_count_received,
            "packet_completeness":   packet_completeness,
            "rssi":                  rssi,
            "snr":                   snr,
            "readings":              readings,
            "sensor_statuses":       sensor_statuses,
            "sensor_batteries":      sensor_batteries,
            "packet_quality":        packet_quality,
        }
