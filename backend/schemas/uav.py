from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ConnectedUserOut(BaseModel):
    victim_id: str
    name: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    priority_class: Optional[str] = None


class UAVOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uav_id:            str
    name:              Optional[str] = None
    home_region:       Optional[str] = None
    current_region:    Optional[str] = None
    timestamp:         Optional[str] = None
    latitude:          Optional[float] = None
    longitude:         Optional[float] = None
    altitude:          Optional[float] = None
    battery:           Optional[int] = None
    status:            str = "standby"
    coverage_radius:   float = 800.0
    connected_devices: int = 0
    connected_users:   List[ConnectedUserOut] = []
    connected_victims: List[ConnectedUserOut] = []
    nearby_teams:      int = 0


class UAVUpdateIn(BaseModel):
    uav_id:            str
    timestamp:         str
    latitude:          float
    longitude:         float
    altitude:          float
    battery:           int
    status:            str
    coverage_radius:   float
    connected_devices: int
    name:              Optional[str] = None
    home_region:       Optional[str] = None
    current_region:    Optional[str] = None
