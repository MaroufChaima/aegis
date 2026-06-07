from sqlalchemy import Column, Integer, Text, Float, ForeignKey
from database import Base


class VictimPhysiologicalProfile(Base):
    """Stores personalized physiological normal ranges for each victim. These ranges are used by the personalized decision engine to distinguish between globally abnormal values and values that are abnormal specifically for this individual. For example, an athlete with HR of 45 bpm is within their personal normal range even though 45 is globally low."""

    __tablename__ = "victim_physiological_profiles"

    profile_id             = Column(Integer, primary_key=True, autoincrement=True)
    victim_id              = Column(Text, ForeignKey("victims.victim_id"), nullable=False)
    hr_baseline            = Column(Float, nullable=True)   # individual resting heart rate
    hr_normal_min          = Column(Float, nullable=True)   # personal minimum normal HR e.g. athlete: 40
    hr_normal_max          = Column(Float, nullable=True)   # personal maximum normal HR e.g. child: 120
    spo2_normal_min        = Column(Float, nullable=True)   # minimum acceptable SpO2 percentage
    temp_normal_min        = Column(Float, nullable=True)   # minimum normal body temperature in Celsius
    temp_normal_max        = Column(Float, nullable=True)   # maximum normal body temperature in Celsius
    rr_normal_min          = Column(Float, nullable=True)   # minimum respiratory rate breaths per minute
    rr_normal_max          = Column(Float, nullable=True)   # maximum respiratory rate breaths per minute
    glucose_normal_min     = Column(Float, nullable=True)   # NULL for non-diabetic victims
    glucose_normal_max     = Column(Float, nullable=True)   # NULL for non-diabetic victims
    bp_systolic_normal_min = Column(Float, nullable=True)   # minimum systolic blood pressure mmHg
    bp_systolic_normal_max = Column(Float, nullable=True)   # maximum systolic blood pressure mmHg
    notes                  = Column(Text, nullable=True)    # clinical notes e.g. athlete lower resting HR is normal
    updated_at             = Column(Text, nullable=True)    # ISO timestamp string
