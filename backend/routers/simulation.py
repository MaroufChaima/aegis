"""
Simulation control router.

Exposes four endpoints that let the dashboard control the running simulator
by reading/writing the shared simulator_state.json file at the repository root.

Endpoints:
    GET  /api/simulation/status    — return current running state and active scenario
    POST /api/simulation/pause     — write {"running": false} → simulator stops emitting
    POST /api/simulation/resume    — write {"running": true}  → simulator resumes
    POST /api/simulation/scenario  — write scenario name → simulator applies it next tick

The state file lives at <repo_root>/simulator_state.json.  Both the simulator
(simulator/simulator.py) and this router resolve the path relative to their own
__file__ location so neither depends on the current working directory.
"""

import json
import pathlib
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Resolve repo root regardless of where uvicorn was launched from
_STATE_FILE = pathlib.Path(__file__).parent.parent.parent / "simulator_state.json"

_VALID_SCENARIOS = {
    "sos_wave",
    "mass_casualty",
    "uav_failure",
    "gradual_deterioration",
    "network_partition",
}

_DEFAULT_STATE = {"running": True, "scenario": None}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_state() -> dict:
    """Read and parse simulator_state.json; return defaults on any error.

    Returns:
        Dict with at least the keys ``running`` (bool) and ``scenario`` (str|None).
    """
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return dict(_DEFAULT_STATE)


def _write_state(state: dict) -> None:
    """Persist state dict to simulator_state.json.

    Args:
        state: Dict to serialise.

    Raises:
        HTTPException 500: If the file cannot be written.
    """
    try:
        _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not write state file: {exc}")


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------

class ScenarioRequest(BaseModel):
    """Body for POST /api/simulation/scenario."""

    name: Literal[
        "sos_wave",
        "mass_casualty",
        "uav_failure",
        "gradual_deterioration",
        "network_partition",
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def get_status():
    """Return the current simulator running state and pending scenario.

    Returns:
        JSON with ``running`` (bool), ``scenario`` (str | null).
    """
    return _read_state()


@router.post("/pause")
def pause_simulator():
    """Write running=false to the state file, causing the simulator to pause.

    The simulator checks this flag at the start of each tick and skips
    emission while paused.

    Returns:
        JSON confirmation.
    """
    state = _read_state()
    state["running"] = False
    _write_state(state)
    return {"status": "paused"}


@router.post("/resume")
def resume_simulator():
    """Write running=true to the state file, resuming the simulator.

    Returns:
        JSON confirmation.
    """
    state = _read_state()
    state["running"] = True
    _write_state(state)
    return {"status": "running"}


@router.post("/scenario")
def trigger_scenario(body: ScenarioRequest):
    """Queue a named scenario for the simulator to apply on its next tick.

    The simulator reads the state file at the start of each tick. If
    ``scenario`` is non-null, it dispatches to the matching function,
    then clears the field so the scenario only fires once.

    Args:
        body: ScenarioRequest with ``name`` field.

    Returns:
        JSON with ``queued`` scenario name and current ``running`` state.
    """
    state = _read_state()
    state["scenario"] = body.name
    _write_state(state)
    return {"queued": body.name, "running": state.get("running", True)}
