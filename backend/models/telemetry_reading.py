from sqlalchemy import Column, Integer, Text, Float, ForeignKey
from database import Base


class TelemetryReading(Base):
    """Stores one sensor measurement from one coordinator packet. There is one TelemetryReading row per sensor per packet. This normalized design allows heterogeneous sensors across different victim profiles without schema changes. The dual anomaly flags (is_anomaly_global and is_anomaly_personal) enable the research finding that globally normal values can be abnormal for specific individuals and vice versa."""

    __tablename__ = "telemetry_readings"

    reading_id            = Column(Integer, primary_key=True, autoincrement=True)
    packet_id             = Column(Integer, ForeignKey("coordinator_packets.packet_id"), nullable=False)
    victim_id             = Column(Text, ForeignKey("victims.victim_id"), nullable=False)
    sensor_type_id        = Column(Text, ForeignKey("sensor_types.sensor_type_id"), nullable=False)
    timestamp             = Column(Text, nullable=True)                    # ISO timestamp
    raw_value             = Column(Float, nullable=True)                   # NULL if sensor failed or was disconnected
    raw_value_present     = Column(Integer, nullable=False, default=0)     # SQLite boolean: 1 if sensor provided a value, 0 if sensor failed. This flag exists because raw_value NULL could mean zero or missing — this flag removes the ambiguity
    imputed_value         = Column(Float, nullable=True)                   # NULL if raw_value was present. Set by imputation pipeline when raw_value is missing
    imputation_method     = Column(Text, nullable=True)                    # NULL | forward_fill | profile_mean | knn. Records which method was used
    imputation_confidence = Column(Float, nullable=True)                   # confidence score 0.0 to 1.0 for the imputed value. NULL if raw value was present
    is_anomaly_global     = Column(Integer, nullable=True, default=0)      # SQLite boolean: 1 if value is outside population-level normal range
    is_anomaly_personal   = Column(Integer, nullable=True, default=0)      # SQLite boolean: 1 if value is outside this specific victims personal normal range
    deviation_score       = Column(Float, nullable=True)                   # how many standard deviations from this victims personal baseline
    sensor_reliability    = Column(Float, nullable=True, default=1.0)      # rolling reliability score 0.0 to 1.0 based on historical failure rate of this sensor instance
