"""
Model registry for AEGIS database. All models must be imported here so SQLAlchemy
can discover them when init_db.py calls Base.metadata.create_all(). Import order
matters: tables referenced by foreign keys must be imported before the tables that
reference them.
"""

from models.sensor_type import SensorType                           # Must be imported first: other models reference this table via foreign key
from models.uav import UAVPosition                                  # UAV model unchanged from original architecture
from models.victim import Victim                                    # New WBAN architecture: victim identity table
from models.victim_profile import VictimPhysiologicalProfile        # New WBAN architecture: depends on Victim
from models.victim_sensor import VictimSensor                       # New WBAN architecture: depends on Victim and SensorType
from models.coordinator_packet import CoordinatorPacket             # New WBAN architecture: depends on Victim
from models.telemetry_reading import TelemetryReading               # New WBAN architecture: depends on CoordinatorPacket, Victim, SensorType
from models.alert import Alert                                      # Alert model: keep existing import
from models.device import Device                                    # LEGACY: keep until M7 cleanup phase
from models.telemetry import Telemetry                              # LEGACY: keep until M7 cleanup phase
