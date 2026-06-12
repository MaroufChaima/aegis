"""
Represents one complete simulated victim including their WBAN coordinator and all
assigned wearable sensors. This is the main unit the simulator loop interacts with —
each tick evolves all sensors and produces one coordinator packet.
"""

from physiological_profile import PhysiologicalProfile
from wearable_sensor import WearableSensor
from wban_coordinator import WBANCoordinator


class VictimWBAN:
    """Represents one complete simulated victim including their WBAN coordinator and
    all assigned wearable sensors. This is the main unit the simulator loop interacts
    with — each tick evolves all sensors and produces one coordinator packet."""

    def __init__(
        self,
        victim_id: str,
        name: str,
        risk_category: str,
        profile: PhysiologicalProfile,
        sensor_type_ids: list,
        uav_relay_id: str,
    ):
        self.victim_id     = victim_id
        self.name          = name
        self.risk_category = risk_category
        self.uav_relay_id  = uav_relay_id
        self.sos_active    = False

        self.sensors = [
            WearableSensor(
                sensor_type_id=sensor_type_id,
                sensor_instance_id=f"{victim_id}-{sensor_type_id.upper().replace(chr(95), chr(45))}-01",
            )
            for sensor_type_id in sensor_type_ids
        ]

        self.coordinator = WBANCoordinator(
            victim_id=victim_id,
            coordinator_id=f"COORD-{victim_id}",
            sensors=self.sensors,
            profile=profile,
            uav_relay_id=uav_relay_id,
        )

    def tick(self):
        self.coordinator.tick()

    def build_packet(self) -> dict:
        return self.coordinator.build_packet(sos_active=self.sos_active)

    @property
    def profile(self):
        return self.coordinator.profile

    @property
    def victim_summary(self) -> str:
        return f"{self.victim_id} ({self.name}, {self.risk_category})"
