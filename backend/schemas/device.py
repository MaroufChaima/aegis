"""
Pydantic schema for the GET /api/victims response shape.
Each item in the response array serialises to this model.
Matches the exact field names and types documented in API_FLOW.md.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional


class DeviceOut(BaseModel):
    """Outbound representation of a single registered device.

    Combines identity fields, AI-computed scores, and the latest
    telemetry vitals so the frontend can render both the priority
    table and the map markers from a single response.
    """

    model_config = ConfigDict(from_attributes=True)

    device_id:      str
    status:         str
    severity_score: int
    priority_class: str
    is_anomaly:     bool
    last_seen:      Optional[str]
    uav_relay_id:   Optional[str]

    # Latest vitals — populated on every upsert
    latitude:       Optional[float]
    longitude:      Optional[float]
    heart_rate:     Optional[int]
    temperature:    Optional[float]
    sos_signal:     bool
    movement:       bool
    rssi:           Optional[int]
    battery:        Optional[int]

    @field_validator("is_anomaly", mode="before")
    @classmethod
    def coerce_anomaly(cls, v) -> bool:
        """Accept INTEGER 0/1 from SQLite and coerce to bool."""
        return bool(v)

    @field_validator("sos_signal", "movement", mode="before")
    @classmethod
    def coerce_bool(cls, v) -> bool:
        """Accept INTEGER 0/1 from SQLite and coerce to bool."""
        return bool(v)
