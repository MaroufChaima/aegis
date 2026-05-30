"""
Stores one record per registered wearable device.
Updated on every ingest: severity score, priority class, anomaly flag,
and last-seen timestamp are written by the AI pipeline after each telemetry
packet arrives.
"""

from sqlalchemy import Column, Integer, Text
from database import Base


class Device(Base):
    __tablename__ = "devices"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    device_id      = Column(Text, unique=True, nullable=False)
    name           = Column(Text)
    status         = Column(Text, default="online")       # online | offline | sos
    severity_score = Column(Integer, default=0)           # 0–100, set by triage scorer
    priority_class = Column(Text, default="P3")           # P1 | P2 | P3
    anomaly_flag   = Column(Integer, default=0)           # 0/1 — set by Isolation Forest
    last_seen      = Column(Text)                         # ISO 8601 timestamp as TEXT
    uav_relay_id   = Column(Text)                         # e.g. "UAV-02"
