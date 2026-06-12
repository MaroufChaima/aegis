"""
Generates realistic physiological sensor readings based on a victim specific medical
profile. Each reading uses the victims personal normal ranges with Gaussian noise to
simulate natural physiological variation. The battery state is tracked across calls
to simulate drain over time.
"""

import numpy as np
import random


class PhysiologicalProfile:
    """Generates realistic physiological sensor readings based on a victim specific
    medical profile. Each reading uses the victims personal normal ranges with Gaussian
    noise to simulate natural physiological variation. The battery state is tracked
    across calls to simulate drain over time."""

    def __init__(
        self,
        victim_id: str,
        risk_category: str,
        hr_baseline: float,
        hr_normal_min: float,
        hr_normal_max: float,
        temp_normal_min: float,
        temp_normal_max: float,
        spo2_normal_min: float,
        rr_normal_min: float,
        rr_normal_max: float,
        glucose_normal_min,
        glucose_normal_max,
        bp_systolic_normal_min: float,
        bp_systolic_normal_max: float,
    ):
        self.victim_id             = victim_id
        self.risk_category         = risk_category
        self.hr_baseline           = hr_baseline
        self.hr_normal_min         = hr_normal_min
        self.hr_normal_max         = hr_normal_max
        self.temp_normal_min       = temp_normal_min
        self.temp_normal_max       = temp_normal_max
        self.spo2_normal_min       = spo2_normal_min
        self.rr_normal_min         = rr_normal_min
        self.rr_normal_max         = rr_normal_max
        self.glucose_normal_min    = glucose_normal_min
        self.glucose_normal_max    = glucose_normal_max
        self.bp_systolic_normal_min = bp_systolic_normal_min
        self.bp_systolic_normal_max = bp_systolic_normal_max

        self._gps_lat = 36.7325 + np.random.uniform(-0.01, 0.01)
        self._gps_lon = 3.0862 + np.random.uniform(-0.01, 0.01)
        self._battery = 100.0

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))

    def generate_reading(self, sensor_type_id: str):
        overrides = getattr(self, "_reading_overrides", None)
        if overrides and sensor_type_id in overrides:
            return overrides[sensor_type_id]

        if sensor_type_id == "rssi" and getattr(self, "_rssi_override", None) is not None:
            return self._rssi_override

        if sensor_type_id == "heart_rate":
            raw = np.random.normal(
                self.hr_baseline,
                (self.hr_normal_max - self.hr_normal_min) * 0.08,
            )
            return self._clamp(raw, self.hr_normal_min * 0.9, self.hr_normal_max * 1.1)

        if sensor_type_id == "spo2":
            raw = np.random.normal((self.spo2_normal_min + 100.0) / 2, 0.5)
            return self._clamp(raw, 85.0, 100.0)

        if sensor_type_id == "temperature":
            raw = np.random.normal(
                (self.temp_normal_min + self.temp_normal_max) / 2, 0.15
            )
            return self._clamp(raw, 34.0, 42.0)

        if sensor_type_id == "blood_pressure_systolic":
            raw = np.random.normal(
                (self.bp_systolic_normal_min + self.bp_systolic_normal_max) / 2, 5.0
            )
            return self._clamp(raw, 60.0, 200.0)

        if sensor_type_id == "blood_pressure_diastolic":
            raw = np.random.normal(75.0, 4.0)
            return self._clamp(raw, 40.0, 120.0)

        if sensor_type_id == "respiratory_rate":
            raw = np.random.normal(
                (self.rr_normal_min + self.rr_normal_max) / 2, 1.5
            )
            return self._clamp(raw, 4.0, 40.0)

        if sensor_type_id == "motion_activity":
            return round(np.random.uniform(0.0, 1.0), 2)

        if sensor_type_id == "fall_detected":
            return 0.0

        if sensor_type_id == "gps_lat":
            return self._gps_lat + np.random.normal(0, 0.0001)

        if sensor_type_id == "gps_lon":
            return self._gps_lon + np.random.normal(0, 0.0001)

        if sensor_type_id == "rssi":
            raw = np.random.normal(-80.0, 8.0)
            return self._clamp(raw, -120.0, 0.0)

        if sensor_type_id == "battery":
            self._battery = max(0.0, self._battery - 0.02)
            return self._battery

        if sensor_type_id == "glucose":
            if self.glucose_normal_min is None:
                return None
            raw = np.random.normal(
                (self.glucose_normal_min + self.glucose_normal_max) / 2, 5.0
            )
            return self._clamp(raw, 40.0, 400.0)

        if sensor_type_id == "ecg_hr_variability":
            raw = np.random.normal(55.0, 10.0)
            return self._clamp(raw, 10.0, 150.0)

        if sensor_type_id == "eeg_alert_index":
            raw = np.random.normal(60.0, 15.0)
            return self._clamp(raw, 0.0, 100.0)

        return None
