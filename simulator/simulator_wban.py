"""
Main WBAN simulator for AEGIS. Run with: python simulator_wban.py. This replaces
simulator_legacy.py. Posts coordinator packets to the backend API every 5 seconds
for all 15 simulated victims. Reads simulator_state.json for pause/scenario control.
"""

import pathlib
import sys
import requests
import time
import json
import datetime

from victim_factory import create_all_victims
from scenarios_wban import SCENARIO_REGISTRY_WBAN, apply_tick_effects

API_URL               = "http://localhost:8000/api/v2/ingest"
EMIT_INTERVAL_SECONDS = 5
STATE_FILE            = pathlib.Path(__file__).parent.parent / "simulator_state.json"
_DEFAULT_STATE        = {"running": True, "scenario": None}


def _read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
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
            print(
                f"  OK: {packet['victim_id']} "
                f"completeness={packet['packet_completeness']:.2f}"
            )
            return True
        else:
            print(
                f"  WARN: {packet['victim_id']} got status {response.status_code}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ERROR: Cannot connect to backend at {API_URL}")
        return False
    except Exception as e:
        print(f"  ERROR: {packet['victim_id']} failed: {e}")
        return False


def run_simulator():
    print("AEGIS WBAN Simulator starting...", flush=True)
    print(f"  State file: {STATE_FILE.resolve()}", flush=True)
    print(f"  Scenarios:  {', '.join(sorted(SCENARIO_REGISTRY_WBAN))}", flush=True)
    if not STATE_FILE.exists():
        _write_state(_DEFAULT_STATE)

    victims = create_all_victims()
    print(f"Created {len(victims)} victims")

    tick_count = 0

    while True:
        print(
            f"\n--- Tick {tick_count} at {datetime.datetime.utcnow().isoformat()} ---"
        )

        state = _read_state()

        if not state.get("running", True):
            print("  PAUSED — waiting for resume…")
            time.sleep(EMIT_INTERVAL_SECONDS)
            continue

        scenario_name = state.get("scenario")
        if scenario_name:
            handler = SCENARIO_REGISTRY_WBAN.get(scenario_name)
            try:
                if handler:
                    result = handler(victims)
                    print(f"[SCENARIO] {scenario_name} applied -> {result}", flush=True)
                else:
                    print(f"[SCENARIO] Unknown scenario: {scenario_name}", flush=True)
            except Exception as exc:
                print(f"[SCENARIO] {scenario_name} failed: {exc}", flush=True)
            finally:
                state["scenario"] = None
                _write_state(state)

        apply_tick_effects(victims)

        for victim in victims:
            victim.tick()
            packet = victim.build_packet()
            post_packet(packet)

        tick_count += 1
        time.sleep(EMIT_INTERVAL_SECONDS)


if __name__ == "__main__":
    # Windows consoles default to cp1252; force UTF-8-safe ASCII logging.
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    run_simulator()
