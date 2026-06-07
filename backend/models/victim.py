from sqlalchemy import Column, Integer, Text
from database import Base


class Victim(Base):
    """Represents a disaster victim tracked by the AEGIS platform. Central identity table for the WBAN architecture. Each victim owns multiple wearable sensors connected through a WBAN coordinator node."""

    __tablename__ = "victims"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    victim_id          = Column(Text, unique=True, nullable=False)            # e.g. "V-001"
    name               = Column(Text, nullable=True)
    age                = Column(Integer, nullable=True)
    gender             = Column(Text, nullable=True)                          # male | female | other
    medical_conditions = Column(Text, nullable=True)                          # JSON array stored as string e.g. ["diabetes"]
    risk_category      = Column(Text, nullable=True)                          # healthy | diabetic | cardiac | neurological | elderly | pregnant | athlete | child
    pregnancy_status   = Column(Integer, nullable=True, default=0)            # SQLite boolean: 0 or 1
    is_athlete         = Column(Integer, nullable=True, default=0)            # SQLite boolean: 0 or 1
    notes              = Column(Text, nullable=True)
    created_at         = Column(Text, nullable=True)                          # ISO timestamp string
