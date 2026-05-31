"""
Pydantic schema for the GET /api/uavs response shape and the
POST /api/uavs/update request body from the simulator.
Matches the API_FLOW.md UAV response and uav_update WebSocket payload.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class UAVOut(BaseModel):
    """Outbound UAV position and status record."""

    model_config = ConfigDict(from_attributes=True)

    uav_id:            str
    timestamp:         Optional[str]
    latitude:          Optional[float]
    longitude:         Optional[float]
    altitude:          Optional[float]
    battery:           Optional[int]
    status:            str
    coverage_radius:   float
    connected_devices: int


class UAVUpdateIn(BaseModel):
    """Inbound UAV position update posted by the simulator each tick."""

    uav_id:            str
    timestamp:         str
    latitude:          float
    longitude:         float
    altitude:          float
    battery:           int
    status:            str
    coverage_radius:   float
    connected_devices: int
