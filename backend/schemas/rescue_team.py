from pydantic import BaseModel
from typing import Optional, List


class RescuerOut(BaseModel):
    rescuer_id: str
    team_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    years_experience: Optional[int] = None


class RescueTeamOut(BaseModel):
    team_id: str
    team_name: str
    team_type: Optional[str] = None
    specialization: Optional[str] = None
    current_region: Optional[str] = None
    status: Optional[str] = "Standby"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    members: List[RescuerOut] = []
    assigned_victims: List[str] = []
    assigned_users: List[str] = []
    assigned_uavs: List[str] = []
    member_count: int = 0
    personnel_count: int = 0
    assigned_victim_count: int = 0


class RescuerDetailOut(RescuerOut):
    team: Optional[RescueTeamOut] = None
