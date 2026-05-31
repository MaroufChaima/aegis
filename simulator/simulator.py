"""
AEGIS Telemetry Simulator — steady-state emission loop.

Tick loop (every EMIT_INTERVAL seconds):
    1. Read simulator_state.json — honour pause and pick up pending scenarios
    2. Apply any per-tick multi-step scenario effects (deterioration, partition)
    3. Evolve all wearable devices → POST each to /api/ingest
    4. Evolve all UAVs → POST each to /api/uavs/update
    5. Sleep EMIT_INTERVAL seconds

Communication with the backend uses a shared JSON file (simulator_state.json)
at the repository root.  The backend writes to it; this process reads and
(when consuming a scenario) rewrites it.

Run from the simulator/ directory:
    python simulator.py
"""

import json
import logging
import pathlib
import time

import requests

from config import DEVICE_IDS, UAV_IDS, EMIT_INTERVAL, API_URL
from device_model import DeviceState, UAVState
from scenarios import SCENARIO_REGISTRY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

INGEST_URL     = f"{API_URL}/api/ingest"
UAV_UPDATE_URL = f"{API_URL}/api/uavs/update"

# simulator_state.json lives one level up (repo root), next to both
# simulator/ and backend/ directories so both processes can reach it.
STATE_FILE = pathlib.Path(__file__).parent.parent / "simulator_state.json"

_DEFAULT_STATE = {"running": True, "scenario": None}


# ---------------------------------------------------------------------------
# State file helpers
# ---------------------------------------------------------------------------

def _read_state() -> dict:
    """Read simulator_state.json; return default state on any read error."""
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return dict(_DEFAULT_STATE)


def _write_state(state: dict) -> None:
    """Atomically overwrite simulator_state.json with updated state."""
    try:
        STATE_FILE.write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        log.warning("Could not write state file: %s", exc)


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def post_payload(session: requests.Session, url: str, payload: dict, label: str) -> None:
    """POST one payload to url and log the outcome.

    Logs a one-line summary on success. Logs HTTP status or network errors
    without re-raising so a single failure never halts the loop.

    Args:
        session: Persistent requests.Session for connection reuse.
        url:     Destination endpoint.
        payload: JSON-serialisable dict.
        label:   Short identifier for log lines (device_id or uav_id).
    """
    try:
        resp = session.post(url, json=payload, timeout=4)
        if resp.status_code == 200:
            if "heart_rate" in payload:
                log.info("OK  %s  HR=%s  temp=%s  bat=%s%%",
                         label, payload["heart_rate"],
                         payload["temperature"], payload["battery"])
            else:
                log.info("UAV %s  bat=%s%%  status=%s",
                         label, payload["battery"], payload["status"])
        elif resp.status_code == 409:
            log.warning("DUP %s  duplicate packet discarded", label)
        else:
            log.error("ERR %s  HTTP %s — %s", label, resp.status_code, resp.text[:120])
    except requests.exceptions.ConnectionError:
        log.error("ERR %s  connection refused — is the backend running?", label)
    except requests.exceptions.Timeout:
        log.error("ERR %s  request timed out", label)
    except requests.exceptions.RequestException as exc:
        log.error("ERR %s  unexpected error: %s", label, exc)


# ---------------------------------------------------------------------------
# Per-tick multi-step scenario effects
# ---------------------------------------------------------------------------

def _apply_tick_effects(devices: dict) -> None:
    """Advance and expire any ongoing multi-tick scenario effects.

    Called once per tick *before* evolve() so updated baselines are
    reflected in the same tick's payload.

    Managed effects:
    - Gradual deterioration: nudge _baseline_hr upward each tick until
      _deterioration_ticks reaches 0.
    - Network partition: count down _partition_ticks; restore original
      RSSI baseline when the timer expires.

    Args:
        devices: Mapping of device_id → DeviceState.
    """
    for dev in devices.values():
        # Gradual deterioration
        ticks = getattr(dev, "_deterioration_ticks", 0)
        if ticks > 0:
            rate = getattr(dev, "_deterioration_rate", 9)
            dev._baseline_hr = min(200, dev._baseline_hr + rate)
            dev._deterioration_ticks = ticks - 1
            if dev._deterioration_ticks == 0:
                log.info("SCENARIO  gradual_deterioration expired for %s  final_baseline_hr=%d",
                         dev.device_id, dev._baseline_hr)

        # Network partition countdown
        pticks = getattr(dev, "_partition_ticks", 0)
        if pticks > 0:
            dev._partition_ticks = pticks - 1
            if dev._partition_ticks == 0:
                # Restore original RSSI baseline
                original = getattr(dev, "_pre_partition_rssi", dev._baseline_rssi)
                dev._baseline_rssi = original
                log.info("SCENARIO  network_partition expired for %s  rssi restored to %d",
                         dev.device_id, dev._baseline_rssi)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run() -> None:
    """Initialise all devices and UAVs then run the main emission loop.

    On every tick:
    1. Reads simulator_state.json to check pause state and pending scenario.
    2. If paused, skips emission and sleeps.
    3. If a scenario name is present, dispatches to SCENARIO_REGISTRY and
       clears it from the state file so it only fires once.
    4. Applies per-tick multi-step effects (deterioration, partition).
    5. Evolves and emits all wearable device payloads.
    6. Computes UAV-device relay counts, evolves and emits all UAV payloads.
    """
    # Ensure state file exists with defaults on first run
    if not STATE_FILE.exists():
        _write_state(_DEFAULT_STATE)
        log.info("Created %s", STATE_FILE)

    devices = {did: DeviceState(did) for did in DEVICE_IDS}
    uavs    = {uid: UAVState(uid)    for uid in UAV_IDS}

    log.info(
        "Simulator started — %d devices, %d UAVs, posting every %ds",
        len(devices), len(uavs), EMIT_INTERVAL,
    )

    with requests.Session() as session:
        tick = 0
        while True:
            tick += 1
            log.info("── tick %d ──────────────────────────────", tick)

            # --- Read shared state ---
            state = _read_state()

            # --- Pause check ---
            if not state.get("running", True):
                log.info("PAUSED — waiting for resume…")
                time.sleep(EMIT_INTERVAL)
                continue

            # --- Scenario dispatch ---
            scenario_name = state.get("scenario")
            if scenario_name:
                handler = SCENARIO_REGISTRY.get(scenario_name)
                if handler:
                    result = handler(devices, uavs)
                    log.info("SCENARIO  %s  applied → %s", scenario_name, result)
                else:
                    log.warning("SCENARIO  unknown name: %r — ignored", scenario_name)
                # Always clear after consumption regardless of success
                state["scenario"] = None
                _write_state(state)

            # --- Per-tick multi-step effects ---
            _apply_tick_effects(devices)

            # --- Wearable devices ---
            for device in devices.values():
                payload = device.evolve()
                post_payload(session, INGEST_URL, payload, payload["device_id"])

            # --- UAVs ---
            relay_counts: dict[str, int] = {uid: 0 for uid in UAV_IDS}
            for dev in devices.values():
                if dev.uav_relay_id in relay_counts:
                    relay_counts[dev.uav_relay_id] += 1

            for uav in uavs.values():
                payload = uav.evolve(connected_devices=relay_counts[uav.uav_id])
                post_payload(session, UAV_UPDATE_URL, payload, payload["uav_id"])

            time.sleep(EMIT_INTERVAL)


if __name__ == "__main__":
    run()
