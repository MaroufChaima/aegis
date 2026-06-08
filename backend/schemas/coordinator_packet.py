"""
Pydantic schemas for WBAN coordinator packet ingestion. CoordinatorPacketIn validates
incoming packets from the simulator. The readings field uses Dict[str, Optional[float]]
rather than fixed fields because different victim profiles have different sensor sets —
a diabetic victim sends a glucose reading that a healthy victim does not have. This
flexible dict design allows one schema to handle all 15 victim profiles without
modification.
"""

from pydantic import BaseModel, field_validator
from typing import Dict, Optional


class CoordinatorPacketIn(BaseModel):
    victim_id:              str                          # e.g. V-007
    coordinator_id:         str                          # e.g. COORD-V-007
    uav_relay_id:           Optional[str] = None
    timestamp:              str                          # ISO timestamp string from the coordinator device
    sensor_count_expected:  int
    sensor_count_received:  int
    packet_completeness:    float                        # ratio 0.0 to 1.0
    rssi:                   Optional[float] = None
    snr:                    Optional[float] = None
    readings:               Dict[str, Optional[float]]  # keys are sensor_type_ids, values are floats or None if sensor failed
    sensor_statuses:        Optional[Dict[str, str]] = None  # keys are sensor_type_ids, values are active | disconnected | damaged | battery_depleted | degraded
    packet_quality:         Optional[str] = None         # good | degraded | poor

    @field_validator("packet_completeness")
    @classmethod
    def validate_completeness(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("packet_completeness must be between 0.0 and 1.0")
        return v

    @field_validator("victim_id")
    @classmethod
    def validate_victim_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("victim_id cannot be empty")
        return v


class CoordinatorPacketOut(BaseModel):
    status:              str
    victim_id:           str
    packet_id:           Optional[int] = None
    packet_completeness: float
    readings_stored:     int           # how many telemetry_readings rows were created
    message:             Optional[str] = None
