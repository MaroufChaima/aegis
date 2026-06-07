from sqlalchemy import Column, Integer, Text, Float
from database import Base


class SensorType(Base):
    """Reference table for all sensor types supported by the WBAN architecture. Adding a new sensor type requires only inserting a new row here — no schema changes needed. This design allows the system to support future sensors without database redesign."""

    __tablename__ = "sensor_types"

    sensor_type_id    = Column(Text, primary_key=True)              # e.g. heart_rate, glucose, ecg_hr_variability
    display_name      = Column(Text, nullable=False)                # Human readable name e.g. Heart Rate Monitor
    unit              = Column(Text, nullable=True)                 # measurement unit e.g. bpm, Celsius, percent
    category          = Column(Text, nullable=True)                 # standard | specialized
    normal_min_global = Column(Float, nullable=True)               # population-level minimum used as fallback
    normal_max_global = Column(Float, nullable=True)               # population-level maximum used as fallback
    is_critical       = Column(Integer, nullable=True, default=0)  # SQLite boolean: 1 if this sensor directly affects triage score
    description       = Column(Text, nullable=True)
