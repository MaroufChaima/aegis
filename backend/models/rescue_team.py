from sqlalchemy import Column, Float, Integer, Text, ForeignKey
from database import Base


class RescueTeam(Base):
    __tablename__ = "rescue_teams"

    team_id         = Column(Text, primary_key=True)
    team_name       = Column(Text, nullable=False)
    team_type       = Column(Text)  # civil_protection | firefighters | medical | police | gendarmerie | search_rescue
    specialization  = Column(Text)
    current_region  = Column(Text)
    status          = Column(Text, default="Standby")  # Active | Standby | Out of Service
    latitude        = Column(Float)
    longitude       = Column(Float)


class Rescuer(Base):
    __tablename__ = "rescuers"

    rescuer_id        = Column(Text, primary_key=True)
    team_id           = Column(Text, ForeignKey("rescue_teams.team_id"), nullable=False)
    first_name        = Column(Text)
    last_name         = Column(Text)
    role              = Column(Text)
    age               = Column(Integer)
    phone             = Column(Text)
    years_experience  = Column(Integer)


class TeamVictimAssignment(Base):
    __tablename__ = "team_victim_assignments"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    team_id     = Column(Text, ForeignKey("rescue_teams.team_id"), nullable=False)
    victim_id   = Column(Text, nullable=False)
    assigned_at = Column(Text)


class TeamUAVAssignment(Base):
    __tablename__ = "team_uav_assignments"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    team_id     = Column(Text, ForeignKey("rescue_teams.team_id"), nullable=False)
    uav_id      = Column(Text, nullable=False)
    assigned_at = Column(Text)
