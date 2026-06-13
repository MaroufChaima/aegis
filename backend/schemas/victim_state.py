from pydantic import BaseModel
from typing import Optional


class VictimStateOut(BaseModel):
    victim_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    risk_category: Optional[str] = None
    medical_conditions: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    home_region: Optional[str] = None
    current_region: Optional[str] = None
    emergency_status: Optional[str] = 'normal'
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
    altitude_m: Optional[float] = None
    rssi: Optional[float] = None
    uav_relay_id: Optional[str] = None
    uav_backup_ids: Optional[str] = '[]'
    packet_completeness: Optional[float] = None
    status: Optional[str] = 'online'
    last_seen: Optional[str] = None
    last_packet_id: Optional[int] = None

    class Config:
        from_attributes = True
