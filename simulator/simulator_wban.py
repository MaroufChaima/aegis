"""
Main WBAN simulator for AEGIS. Run with: python simulator_wban.py. This replaces
simulator_legacy.py. Posts coordinator packets to the backend API every 5 seconds
for all 15 simulated victims.
"""

import requests
import time
import json
import datetime
import random

from victim_factory import create_all_victims

API_URL                 = "http://localhost:8000/api/v2/ingest-stub"
EMIT_INTERVAL_SECONDS   = 5
UAV_EMIT_INTERVAL_TICKS = 2


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
    print("AEGIS WBAN Simulator starting...")
    victims = create_all_victims()
    print(f"Created {len(victims)} victims")

    tick_count = 0

    while True:
        print(
            f"\n--- Tick {tick_count} at {datetime.datetime.utcnow().isoformat()} ---"
        )

        for victim in victims:
            victim.tick()
            packet = victim.build_packet()
            post_packet(packet)

        if tick_count % 300 == 0 and tick_count > 0:
            victim = random.choice(victims)
            random.choice(victim.sensors).failure_probability_per_tick = 0.95
            print(f"[SCENARIO] Forcing sensor failure on {victim.victim_summary}")

        tick_count += 1
        time.sleep(EMIT_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_simulator()
