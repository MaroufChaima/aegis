"""
Main WBAN simulator — ticks users + UAVs for active region only.
"""

import pathlib
import sys
import requests
import time
import json
import datetime

from victim_factory import create_all_victims
from scenarios_wban import SCENARIO_REGISTRY_WBAN, apply_tick_effects
from uav_wban import create_uavs
from uav_assign import assign_users_to_uavs
from demo_config import DEFAULT_REGION

API_URL = "http://localhost:8000/api/v2/ingest"
EMIT_INTERVAL_SECONDS = 5
STATE_FILE = pathlib.Path(__file__).parent.parent / "simulator_state.json"
_DEFAULT_STATE = {"running": True, "scenario": None, "region": DEFAULT_REGION, "emergency_mode": False}


def _read_state() -> dict:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        state.setdefault("region", DEFAULT_REGION)
        state.setdefault("emergency_mode", False)
        return state
    except FileNotFoundError:
        return dict(_DEFAULT_STATE)
    except Exception as exc:
        print(f"  WARN: Could not read state file ({exc}); using defaults")
        return dict(_DEFAULT_STATE)


def _write_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"  WARN: Could not write state file: {exc}")


def post_packet(packet: dict) -> bool:
    try:
        response = requests.post(API_URL, json=packet, timeout=5)
        if response.status_code == 200:
            print(f"  OK: {packet['victim_id']} completeness={packet['packet_completeness']:.2f}")
            return True
        print(f"  WARN: {packet['victim_id']} got status {response.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ERROR: Cannot connect to backend at {API_URL}")
        return False
    except Exception as e:
        print(f"  ERROR: {packet['victim_id']} failed: {e}")
        return False


def _reload_region(region_key: str, emergency_mode: bool):
    victims = create_all_victims(region_key)
    uavs = create_uavs(region_key, emergency_mode)
    return victims, uavs


def run_simulator():
    print("AEGIS WBAN Simulator starting...", flush=True)
    if not STATE_FILE.exists():
        _write_state(_DEFAULT_STATE)

    state = _read_state()
    region_key = state.get("region", DEFAULT_REGION)
    emergency_mode = state.get("emergency_mode", False)
    victims, uavs = _reload_region(region_key, emergency_mode)
    print(f"Region {region_key}: {len(victims)} users, {len(uavs)} UAVs (emergency={emergency_mode})")

    tick_count = 0
    current_region = region_key
    current_emergency = emergency_mode

    while True:
        print(f"\n--- Tick {tick_count} at {datetime.datetime.utcnow().isoformat()} ---")
        state = _read_state()

        if not state.get("running", True):
            print("  PAUSED")
            time.sleep(EMIT_INTERVAL_SECONDS)
            continue

        region_key = state.get("region", DEFAULT_REGION)
        emergency_mode = state.get("emergency_mode", False)
        scenario_name = state.get("scenario")

        if region_key != current_region or emergency_mode != current_emergency:
            victims, uavs = _reload_region(region_key, emergency_mode or bool(scenario_name))
            current_region = region_key
            current_emergency = emergency_mode

        for u in uavs:
            u.set_emergency_mode(emergency_mode or bool(scenario_name))

        if scenario_name:
            handler = SCENARIO_REGISTRY_WBAN.get(scenario_name)
            try:
                if handler:
                    result = handler(victims, uavs) if scenario_name == "uav_failure" else handler(victims)
                    print(f"[SCENARIO] {scenario_name} -> {result}", flush=True)
                    for u in uavs:
                        u.set_emergency_mode(True)
            except Exception as exc:
                print(f"[SCENARIO] {scenario_name} failed: {exc}", flush=True)
            finally:
                state["scenario"] = None
                _write_state(state)

        apply_tick_effects(victims)
        assign_users_to_uavs(victims, uavs)

        relay_counts = {}
        for v in victims:
            if v.uav_relay_id:
                relay_counts[v.uav_relay_id] = relay_counts.get(v.uav_relay_id, 0) + 1

        for uav in uavs:
            uav.tick(relay_counts.get(uav.uav_id, 0))
            uav.post_update()

        for victim in victims:
            victim.tick()
            post_packet(victim.build_packet())

        tick_count += 1
        time.sleep(EMIT_INTERVAL_SECONDS)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    run_simulator()
