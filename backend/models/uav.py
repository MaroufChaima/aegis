"""
Stores the current position and status of each simulated UAV. Rows are upserted
(not appended) on every UAV tick: device_id is UNIQUE so each UAV always has
exactly one current-state row in this table.
"""

from sqlalchemy import Column, Float, Integer, Text
from database import Base


class UAVPosition(Base):
    __tablename__ = "uav_positions"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    uav_id            = Column(Text, unique=True, nullable=False)  # e.g. "UAV-01"
    timestamp         = Column(Text)               # ISO 8601 as TEXT; updated each tick
    latitude          = Column(Float)
    longitude         = Column(Float)
    altitude          = Column(Float)              # metres above ground
    battery           = Column(Integer)            # 0–100 percent
    status            = Column(Text, default="active")  # active | returning | offline
    coverage_radius   = Column(Float, default=800.0)    # metres
    connected_devices = Column(Integer, default=0)      # devices currently relaying through this UAV
