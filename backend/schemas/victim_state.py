from pydantic import BaseModel
from typing import Optional


class VictimStateOut(BaseModel):
    """Response schema for victim current state. Combines victim identity fields from the victims table with operational state fields from victim_current_state. Used by GET /api/victims and GET /api/victims/{id}."""

    victim_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    risk_category: Optional[str] = None
    medical_conditions: Optional[str] = None
    severity_score: Optional[int] = 0
    priority_class: Optional[str] = 'P3'
    is_anomaly: Optional[int] = 0
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    spo2: Optional[float] = None
    blood_pressure_systolic: Optional[float] = None
    blood_pressure_diastolic: Optional[float] = None
    glucose: Optional[float] = None
    respiratory_rate: Optional[float] = None
    battery: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    rssi: Optional[float] = None
    uav_relay_id: Optional[str] = None
    sos_active: Optional[int] = 0
    packet_completeness: Optional[float] = None
    status: Optional[str] = 'online'
    last_seen: Optional[str] = None
    last_packet_id: Optional[int] = None

    class Config:
        from_attributes = True
