"""
Pydantic schemas for the new WBAN victim API responses.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class VictimProfileOut(BaseModel):
    """Complete victim profile including personalized physiological thresholds.
    Returned by GET /api/victims/{victim_id}/profile"""

    model_config = ConfigDict(from_attributes=True)

    victim_id:              str
    name:                   Optional[str] = None
    age:                    Optional[int] = None
    gender:                 Optional[str] = None
    medical_conditions:     Optional[str] = None    # JSON array as string
    risk_category:          Optional[str] = None
    pregnancy_status:       Optional[int] = None
    is_athlete:             Optional[int] = None
    notes:                  Optional[str] = None
    hr_baseline:            Optional[float] = None
    hr_normal_min:          Optional[float] = None
    hr_normal_max:          Optional[float] = None
    spo2_normal_min:        Optional[float] = None
    temp_normal_min:        Optional[float] = None
    temp_normal_max:        Optional[float] = None
    rr_normal_min:          Optional[float] = None
    rr_normal_max:          Optional[float] = None
    glucose_normal_min:     Optional[float] = None
    glucose_normal_max:     Optional[float] = None
    bp_systolic_normal_min: Optional[float] = None
    bp_systolic_normal_max: Optional[float] = None
    profile_notes:          Optional[str] = None
    assigned_sensor_count:  Optional[int] = None
    assigned_sensors:       Optional[List[str]] = None


class VictimSummaryOut(BaseModel):
    """Summary victim information for dashboard table. Returned by GET /api/victims"""

    model_config = ConfigDict(from_attributes=True)

    victim_id:      str
    name:           Optional[str] = None
    age:            Optional[int] = None
    risk_category:  Optional[str] = None
    severity_score: Optional[int] = 0
    priority_class: Optional[str] = "P3"
    status:         Optional[str] = "online"
