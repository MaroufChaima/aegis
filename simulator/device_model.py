"""
DeviceState — mutable runtime state for one simulated wearable device.

Each instance holds the current vitals for a single device and exposes an
evolve() method that advances state by one tick, returning a dict that
matches the TelemetryIn schema exactly.
"""

import random
from datetime import datetime, timezone

from config import ZONE_CENTER, ZONE_RADIUS_DEG, UAV_IDS


class DeviceState:
    """Simulates the physical and physiological state of one wearable device.

    Baseline vitals are randomised at construction to give each device a
    distinct "normal" profile. Every call to evolve() adds Gaussian noise,
    drifts position, and drains the battery slightly.
    """

    def __init__(self, device_id: str) -> None:
        """Initialise a device with randomised baseline vitals.

        Args:
            device_id: Unique identifier string, e.g. "WB-007".
        """
        self.device_id = device_id

        # Assign device to one of the four UAVs in round-robin fashion
        idx = int(device_id.split("-")[1]) - 1
        self.uav_relay_id = UAV_IDS[idx % len(UAV_IDS)]

        # Scatter devices randomly within the zone radius
        self.latitude  = ZONE_CENTER[0] + random.uniform(-ZONE_RADIUS_DEG, ZONE_RADIUS_DEG)
        self.longitude = ZONE_CENTER[1] + random.uniform(-ZONE_RADIUS_DEG, ZONE_RADIUS_DEG)

        # Baseline vitals — each device has its own "normal" to make noise realistic
        self._baseline_hr   = random.randint(65, 85)      # bpm
        self._baseline_temp = round(random.uniform(36.4, 37.4), 1)  # °C
        self._baseline_rssi = random.randint(-88, -65)    # dBm
        self._baseline_snr  = round(random.uniform(5.0, 10.0), 1)

        # Mutable current state
        self.heart_rate  = float(self._baseline_hr)
        self.temperature = self._baseline_temp
        self.rssi        = float(self._baseline_rssi)
        self.snr         = self._baseline_snr
        self.battery     = float(random.randint(80, 100))
        self.sos_signal  = False
        self.movement    = True

    def evolve(self) -> dict:
        """Advance state by one tick and return a TelemetryIn-compatible dict.

        Changes applied each tick:
        - Heart rate:   Gaussian noise, std=5 bpm, clamped 30–200
        - Temperature:  Gaussian noise, std=0.2 °C, clamped 30–43
        - GPS:          Random walk ±0.0001 degrees per axis (victim movement)
        - RSSI/SNR:     Small random jitter to simulate signal variation
        - Battery:      Drains 0.01% per tick (flat discharge model)
        - Movement:     Remains True in steady-state (scenarios will override)

        Returns:
            Dict with all 12 fields required by the TelemetryIn Pydantic schema.
        """
        # Gaussian noise on vitals
        self.heart_rate  = round(random.gauss(self._baseline_hr, 5))
        self.heart_rate  = max(30, min(200, self.heart_rate))

        self.temperature = random.gauss(self._baseline_temp, 0.2)
        self.temperature = round(max(30.0, min(43.0, self.temperature)), 2)

        # GPS random walk — victim is moving slowly in the field
        self.latitude  += random.uniform(-0.0001, 0.0001)
        self.longitude += random.uniform(-0.0001, 0.0001)

        # Signal quality jitter
        self.rssi = int(random.gauss(self._baseline_rssi, 3))
        self.snr  = round(random.gauss(self._baseline_snr, 0.5), 1)

        # Flat battery drain
        self.battery = round(max(0.0, self.battery - 0.01), 4)

        return {
            "device_id":    self.device_id,
            "timestamp":    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude":     round(self.latitude, 6),
            "longitude":    round(self.longitude, 6),
            "heart_rate":   int(self.heart_rate),
            "temperature":  self.temperature,
            "sos_signal":   self.sos_signal,
            "movement":     self.movement,
            "rssi":         self.rssi,
            "snr":          self.snr,
            "battery":      int(self.battery),
            "uav_relay_id": self.uav_relay_id,
        }
