from sqlalchemy import Column, Integer, Text, ForeignKey
from database import Base


class VictimSensor(Base):
    """Records which sensor types are assigned to each victim based on their medical profile. A healthy adult has 10 standard sensors. A diabetic victim has 11 sensors including glucose. A cardiac victim has 11 sensors including ECG. This table enables automatic sensor assignment based on victim profile at simulation startup."""

    __tablename__ = "victim_sensors"

    assignment_id      = Column(Integer, primary_key=True, autoincrement=True)
    victim_id          = Column(Text, ForeignKey("victims.victim_id"), nullable=False)
    sensor_type_id     = Column(Text, ForeignKey("sensor_types.sensor_type_id"), nullable=False)
    sensor_instance_id = Column(Text, nullable=True)             # unique device identifier e.g. V-001-HR-01
    is_active          = Column(Integer, nullable=True, default=1)  # SQLite boolean: 1=active 0=inactive
    failure_mode       = Column(Text, nullable=True)             # NULL | damaged | battery_depleted | disconnected
    assigned_at        = Column(Text, nullable=True)             # ISO timestamp string
    notes              = Column(Text, nullable=True)
