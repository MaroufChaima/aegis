"""
AEGIS Telemetry Simulator — steady-state emission loop.

Instantiates one DeviceState per device, then runs a continuous tick loop:
    1. Evolve all devices (advance vitals by one tick)
    2. POST each device's payload to POST /api/ingest
    3. Log success or HTTP/network errors without crashing
    4. Sleep EMIT_INTERVAL seconds before the next tick

Run from the simulator/ directory:
    python simulator.py
"""

import logging
import time

import requests

from config import DEVICE_IDS, EMIT_INTERVAL, API_URL
from device_model import DeviceState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

INGEST_URL = f"{API_URL}/api/ingest"


def post_payload(session: requests.Session, payload: dict) -> None:
    """POST one telemetry payload to the backend ingest endpoint.

    Logs a one-line summary on success. Logs the HTTP status or network error
    on failure without re-raising, so a single failing device never halts the
    loop for the other devices.

    Args:
        session: Persistent requests.Session for connection reuse.
        payload: Dict matching the TelemetryIn schema.
    """
    device_id = payload["device_id"]
    try:
        resp = session.post(INGEST_URL, json=payload, timeout=4)
        if resp.status_code == 200:
            log.info("OK  %s  HR=%s  temp=%s  bat=%s%%",
                     device_id,
                     payload["heart_rate"],
                     payload["temperature"],
                     payload["battery"])
        elif resp.status_code == 409:
            log.warning("DUP %s  duplicate packet discarded by server", device_id)
        else:
            log.error("ERR %s  HTTP %s — %s", device_id, resp.status_code, resp.text[:120])
    except requests.exceptions.ConnectionError:
        log.error("ERR %s  connection refused — is the backend running?", device_id)
    except requests.exceptions.Timeout:
        log.error("ERR %s  request timed out", device_id)
    except requests.exceptions.RequestException as exc:
        log.error("ERR %s  unexpected error: %s", device_id, exc)


def run() -> None:
    """Initialise all devices and run the main emission loop indefinitely.

    Creates one DeviceState instance per DEVICE_ID, then ticks every
    EMIT_INTERVAL seconds. Each tick evolves every device and fires one
    HTTP POST per device. A requests.Session is reused across all requests
    within a tick to reduce TCP overhead.
    """
    devices = {did: DeviceState(did) for did in DEVICE_IDS}
    log.info("Simulator started — %d devices, posting to %s every %ds",
             len(devices), INGEST_URL, EMIT_INTERVAL)

    with requests.Session() as session:
        tick = 0
        while True:
            tick += 1
            log.info("── tick %d ──────────────────────────────", tick)
            for device in devices.values():
                payload = device.evolve()
                post_payload(session, payload)
            time.sleep(EMIT_INTERVAL)


if __name__ == "__main__":
    run()
