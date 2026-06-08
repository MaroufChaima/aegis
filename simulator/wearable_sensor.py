"""
Simulates a physical wearable sensor that can fail in multiple ways during disaster
conditions. DAMAGED and BATTERY_DEPLETED are permanent failures until manual reset.
DISCONNECTED sensors attempt reconnection each tick with 30 percent probability.
DEGRADED sensors still read but with increased noise.
"""

import random
from enum import Enum


class SensorStatus(Enum):
    ACTIVE            = "active"
    DAMAGED           = "damaged"
    BATTERY_DEPLETED  = "battery_depleted"
    DISCONNECTED      = "disconnected"
    DEGRADED          = "degraded"


class WearableSensor:
    """Simulates a physical wearable sensor that can fail in multiple ways during
    disaster conditions. DAMAGED and BATTERY_DEPLETED are permanent failures until
    manual reset. DISCONNECTED sensors attempt reconnection each tick with 30 percent
    probability. DEGRADED sensors still read but with increased noise."""

    def __init__(
        self,
        sensor_type_id: str,
        sensor_instance_id: str,
        failure_probability_per_tick: float = 0.005,
    ):
        self.sensor_type_id              = sensor_type_id
        self.sensor_instance_id          = sensor_instance_id
        self.failure_probability_per_tick = failure_probability_per_tick
        self.status                      = SensorStatus.ACTIVE
        self.battery                     = 100.0
        self.reliability                 = 1.0
        self._ticks_since_failure        = 0

    def tick(self):
        if self.status in (SensorStatus.BATTERY_DEPLETED, SensorStatus.DAMAGED):
            return

        self.battery = max(0.0, self.battery - 0.03)

        if self.battery < 5.0:
            self.status = SensorStatus.BATTERY_DEPLETED
            return

        failure_prob = self.failure_probability_per_tick
        if self.battery < 20.0:
            failure_prob *= 2.0

        if random.random() < failure_prob:
            self._trigger_failure()

        self.reliability = max(0.0, self.reliability - 0.0001)

    def _trigger_failure(self):
        roll = random.random()
        if roll < 0.4:
            self.status = SensorStatus.DISCONNECTED
        elif roll < 0.7:
            self.status = SensorStatus.DEGRADED
        else:
            self.status = SensorStatus.DAMAGED

    def attempt_reconnect(self) -> bool:
        if self.status is SensorStatus.DISCONNECTED and random.random() < 0.3:
            self.status = SensorStatus.ACTIVE
        return self.status is SensorStatus.ACTIVE

    def read(self) -> bool:
        return self.status in (SensorStatus.ACTIVE, SensorStatus.DEGRADED)

    @property
    def status_string(self) -> str:
        return self.status.value

    @property
    def is_failed(self) -> bool:
        return self.status in (SensorStatus.DAMAGED, SensorStatus.BATTERY_DEPLETED)
