"""
Stores one record per registered wearable device.
Acts as the current-state cache: every ingest upserts the latest vitals,
AI scores, and status so that GET /api/victims needs no JOIN.
History is stored separately in the telemetry table.
"""

from sqlalchemy import Column, Float, Integer, Text
from database import Base


class Device(Base):
    __tablename__ = "devices"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    device_id      = Column(Text, unique=True, nullable=False)
    name           = Column(Text)
    status         = Column(Text, default="online")   # online | offline | sos
    severity_score = Column(Integer, default=0)       # 0–100, updated by triage scorer
    priority_class = Column(Text, default="P3")       # P1 | P2 | P3
    is_anomaly     = Column(Integer, default=0)       # 0/1 — updated by Isolation Forest
    last_seen      = Column(Text)                     # ISO 8601 timestamp as TEXT
    uav_relay_id   = Column(Text)                     # e.g. "UAV-02"

    # Latest vitals — denormalised from the most recent telemetry packet
    latitude       = Column(Float)
    longitude      = Column(Float)
    heart_rate     = Column(Integer)
    temperature    = Column(Float)
    sos_signal     = Column(Integer, default=0)       # 0/1
    movement       = Column(Integer, default=1)       # 0/1
    rssi           = Column(Integer)
    battery        = Column(Integer)
