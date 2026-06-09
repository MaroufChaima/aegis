from sqlalchemy import Column, Integer, Text, Float, ForeignKey
from database import Base


class VictimCurrentState(Base):
    """Stores the current operational state for each victim. This table has exactly one row per victim and is upserted on every successful packet ingestion. It is the single source of truth for the frontend victim table, map markers, and analytics. It replaces the legacy devices table from the original architecture. Using victim_id as the primary key rather than an autoincrement id ensures upsert logic is simple and unambiguous."""

    __tablename__ = 'victim_current_state'

    victim_id = Column(Text, primary_key=True, comment='e.g. V-001. Primary key because there is exactly one current-state row per victim')
    severity_score = Column(Integer, nullable=True, default=0, comment='latest AI triage score 0 to 100')
    priority_class = Column(Text, nullable=True, default='P3', comment='P1 | P2 | P3')
    is_anomaly = Column(Integer, nullable=True, default=0, comment='SQLite boolean: 1 if latest packet flagged as anomalous')
    heart_rate = Column(Float, nullable=True, comment='latest heart_rate reading including imputed values')
    temperature = Column(Float, nullable=True, comment='latest temperature reading including imputed values')
    spo2 = Column(Float, nullable=True, comment='latest SpO2 reading')
    blood_pressure_systolic = Column(Float, nullable=True)
    blood_pressure_diastolic = Column(Float, nullable=True)
    glucose = Column(Float, nullable=True, comment='latest glucose reading for diabetic victims')
    respiratory_rate = Column(Float, nullable=True)
    battery = Column(Float, nullable=True, comment='coordinator node battery percentage')
    gps_lat = Column(Float, nullable=True, comment='latest GPS latitude')
    gps_lon = Column(Float, nullable=True, comment='latest GPS longitude')
    rssi = Column(Float, nullable=True, comment='latest signal strength in dBm')
    uav_relay_id = Column(Text, nullable=True, comment='which UAV is currently serving this victim')
    sos_active = Column(Integer, nullable=True, default=0, comment='SQLite boolean: 1 if SOS is currently active')
    packet_completeness = Column(Float, nullable=True, comment='completeness ratio of the most recent packet 0.0 to 1.0')
    last_packet_quality = Column(Text, nullable=True, comment='good | degraded | poor')
    status = Column(Text, nullable=True, default='online', comment='online | offline | sos')
    last_seen = Column(Text, nullable=True, comment='ISO timestamp of most recent packet')
    last_packet_id = Column(Integer, nullable=True, default=0, comment='packet_id of the most recent coordinator packet')
