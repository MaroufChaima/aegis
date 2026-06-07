from sqlalchemy import Column, Integer, Text, Float, ForeignKey
from database import Base


class CoordinatorPacket(Base):
    """Represents one transmission event from a WBAN coordinator node. A coordinator aggregates readings from all sensors on one victim and sends a single packet. If some sensors failed, packet_completeness will be less than 1.0 and the corresponding telemetry_readings rows will have null raw values. One coordinator_packet has many telemetry_readings (one per sensor type)."""

    __tablename__ = "coordinator_packets"

    packet_id             = Column(Integer, primary_key=True, autoincrement=True)
    victim_id             = Column(Text, ForeignKey("victims.victim_id"), nullable=False)
    coordinator_id        = Column(Text, nullable=True)             # e.g. COORD-V-001
    uav_relay_id          = Column(Text, nullable=True)             # which UAV forwarded this packet
    timestamp             = Column(Text, nullable=False)            # ISO timestamp from the coordinator device
    received_at           = Column(Text, nullable=True)             # ISO timestamp when backend received the packet
    sensor_count_expected = Column(Integer, nullable=True)          # how many sensors this victim should have
    sensor_count_received = Column(Integer, nullable=True)          # how many sensors actually reported a value
    packet_completeness   = Column(Float, nullable=True)            # ratio: sensor_count_received divided by sensor_count_expected, range 0.0 to 1.0
    rssi                  = Column(Float, nullable=True)            # received signal strength indicator in dBm
    snr                   = Column(Float, nullable=True)            # signal to noise ratio
    packet_quality        = Column(Text, nullable=True)             # good | degraded | poor based on completeness and RSSI
    is_duplicate          = Column(Integer, nullable=True, default=0)  # SQLite boolean: 1 if this packet was flagged as a duplicate
    notes                 = Column(Text, nullable=True)
