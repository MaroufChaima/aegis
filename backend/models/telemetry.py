"""
Append-only log of every validated telemetry packet received from the simulator.
Each row is one 5-second reading from one wearable device. Records are never
updated after insertion; the AI pipeline writes is_anomaly and severity_score
at insert time.
"""

from sqlalchemy import Column, Float, Integer, Text
from database import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    device_id      = Column(Text, nullable=False)
    timestamp      = Column(Text, nullable=False)         # ISO 8601 as TEXT
    latitude       = Column(Float)
    longitude      = Column(Float)
    heart_rate     = Column(Integer)
    temperature    = Column(Float)
    sos_signal     = Column(Integer)                      # 0/1
    movement       = Column(Integer)                      # 0/1
    rssi           = Column(Integer)                      # signal strength dBm
    snr            = Column(Float)                        # signal-to-noise ratio
    battery        = Column(Integer)                      # 0–100 percent
    is_anomaly     = Column(Integer, default=0)           # 0/1 — Isolation Forest result
    severity_score = Column(Integer, default=0)           # 0–100 — triage scorer result
