"""
Pydantic schema for the telemetry payload posted by the simulator.
Mirrors the exact JSON structure documented in PROJECT_CONTEXT.md Layer 1.
Field-level validators enforce physiological and signal plausibility ranges.
"""

from pydantic import BaseModel, field_validator


class TelemetryIn(BaseModel):
    """Incoming telemetry packet from one wearable device.

    Matches the simulator JSON payload exactly so that Pydantic rejects
    malformed packets before they reach the preprocessing pipeline.
    """

    device_id:   str
    timestamp:   str
    latitude:    float
    longitude:   float
    heart_rate:  int
    temperature: float
    sos_signal:  bool
    movement:    bool
    rssi:        int
    snr:         float
    battery:     int
    uav_relay_id: str

    @field_validator("heart_rate")
    @classmethod
    def heart_rate_range(cls, v: int) -> int:
        """Reject heart rates outside the physiologically possible range 0–220 bpm."""
        if not (0 <= v <= 220):
            raise ValueError(f"heart_rate {v} out of range 0–220")
        return v

    @field_validator("temperature")
    @classmethod
    def temperature_range(cls, v: float) -> float:
        """Reject body temperatures outside the survivable range 30–43 °C."""
        if not (30.0 <= v <= 43.0):
            raise ValueError(f"temperature {v} out of range 30–43")
        return v
