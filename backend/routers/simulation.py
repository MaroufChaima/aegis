"""
Simulation control router — reads/writes simulator_state.json at repo root.
"""

import json
import pathlib
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data.demo_config import REGIONS, DEFAULT_REGION

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

_STATE_FILE = pathlib.Path(__file__).parent.parent.parent / "simulator_state.json"

_VALID_SCENARIOS = {
    "critical_vitals_wave",
    "mass_casualty",
    "uav_failure",
    "gradual_deterioration",
    "network_partition",
}

_DEFAULT_STATE = {"running": True, "scenario": None, "region": DEFAULT_REGION, "emergency_mode": False}


def _read_state() -> dict:
    try:
        state = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        state.setdefault("region", DEFAULT_REGION)
        state.setdefault("emergency_mode", False)
        return state
    except Exception:
        return dict(_DEFAULT_STATE)


def _write_state(state: dict) -> None:
    try:
        _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not write state file: {exc}")


class ScenarioRequest(BaseModel):
    name: Literal[
        "critical_vitals_wave",
        "mass_casualty",
        "uav_failure",
        "gradual_deterioration",
        "network_partition",
    ]


class RegionRequest(BaseModel):
    region: str


class EmergencyRequest(BaseModel):
    emergency_mode: bool


@router.get("/status")
def get_status():
    state = _read_state()
    region = state.get("region", DEFAULT_REGION)
    return {
        **state,
        "emergency_mode": state.get("emergency_mode", False),
        "region_label": REGIONS.get(region, {}).get("label", region),
        "regions": {k: v["label"] for k, v in REGIONS.items()},
    }


@router.post("/pause")
def pause_simulator():
    state = _read_state()
    state["running"] = False
    _write_state(state)
    return {"status": "paused"}


@router.post("/resume")
def resume_simulator():
    state = _read_state()
    state["running"] = True
    _write_state(state)
    return {"status": "running"}


@router.post("/scenario")
def trigger_scenario(body: ScenarioRequest):
    state = _read_state()
    state["scenario"] = body.name
    _write_state(state)
    return {"queued": body.name, "running": state.get("running", True)}


@router.post("/region")
def set_region(body: RegionRequest):
    if body.region not in REGIONS:
        raise HTTPException(status_code=422, detail=f"Unknown region: {body.region}")
    state = _read_state()
    state["region"] = body.region
    _write_state(state)
    return {
        "region": body.region,
        "region_label": REGIONS[body.region]["label"],
        "running": state.get("running", True),
    }


@router.post("/emergency")
def set_emergency_mode(body: EmergencyRequest):
    state = _read_state()
    state["emergency_mode"] = body.emergency_mode
    _write_state(state)
    return {
        "emergency_mode": body.emergency_mode,
        "region": state.get("region", DEFAULT_REGION),
    }
