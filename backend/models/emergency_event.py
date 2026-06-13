from sqlalchemy import Column, Integer, Text
from database import Base


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    event_id   = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Text, nullable=False)
    region     = Column(Text)
    event_type = Column(Text, nullable=False)  # emergency_start | rescued | deceased | cleared
    timestamp  = Column(Text, nullable=False)
    severity   = Column(Text)
    notes      = Column(Text)
