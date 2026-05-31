"""
Named emergency scenario functions for the AEGIS simulator.

Each function receives the live in-memory dicts of DeviceState and/or
UAVState objects and mutates their attributes directly. The changes
propagate naturally through subsequent evolve() calls, so the dashboard
sees realistic cascading effects without any database writes from here.

Scenario names (used as keys in simulator_state.json):
    sos_wave             — 3 random devices raise SOS simultaneously
    mass_casualty        — 5 devices drop to immediately critical vitals
    uav_failure          — 1 UAV loses power and goes offline
    gradual_deterioration — 1 device's HR climbs steadily toward cardiac range
    network_partition    — 1 device zone loses LoRa connectivity for ~2 minutes

Multi-tick scenarios (gradual_deterioration, network_partition) set special
attributes on device objects. The simulator's main loop is responsible for
advancing or expiring these per-tick effects (see simulator.py).
"""

import random


# ---------------------------------------------------------------------------
# Scenario 1 — SOS Wave
# ---------------------------------------------------------------------------

def sos_wave(devices: dict) -> list[str]:
    """Activate SOS on three randomly chosen devices simultaneously.

    Sets ``sos_signal = True`` on each affected device. The flag persists
    across ticks until another scenario clears it or the device is manually
    reset; this means the triage scorer gives +50 points every tick and
    the alert generator fires SOS alerts for each device.

    Args:
        devices: Mapping of device_id → DeviceState, as held by the simulator.

    Returns:
        List of device_ids that had SOS activated.
    """
    targets = random.sample(list(devices.values()), min(3, len(devices)))
    for dev in targets:
        dev.sos_signal = True
    affected = [d.device_id for d in targets]
    return affected


# ---------------------------------------------------------------------------
# Scenario 2 — Mass Casualty Event
# ---------------------------------------------------------------------------

def mass_casualty(devices: dict) -> list[str]:
    """Drop five devices to life-threatening vitals in a single tick.

    Overrides each affected device's *baseline* so that Gaussian noise on
    subsequent ticks continues to produce critical readings rather than
    recovering to normal. Specifically:
    - HR baseline → 32 bpm  (below 40 → P1 cardiac alert)
    - Temperature baseline → 40.6 °C  (above 39 → severity +15)
    - Movement → False  (motionless victim)

    Args:
        devices: Mapping of device_id → DeviceState.

    Returns:
        List of affected device_ids.
    """
    targets = random.sample(list(devices.values()), min(5, len(devices)))
    for dev in targets:
        dev._baseline_hr   = 32
        dev._baseline_temp = 40.6
        dev.movement       = False
    affected = [d.device_id for d in targets]
    return affected


# ---------------------------------------------------------------------------
# Scenario 3 — UAV Failure
# ---------------------------------------------------------------------------

def uav_failure(uavs: dict) -> str:
    """Force one UAV offline by zeroing its battery and setting status offline.

    The next UAVState.evolve() call will emit battery=0 and status="offline".
    Devices relaying through this UAV continue to show the old relay ID,
    which demonstrates a connectivity gap on the dashboard.

    Args:
        uavs: Mapping of uav_id → UAVState.

    Returns:
        The uav_id of the failed UAV.
    """
    target = random.choice(list(uavs.values()))
    target.battery = 0.0
    target.status  = "offline"
    return target.uav_id


# ---------------------------------------------------------------------------
# Scenario 4 — Gradual Deterioration
# ---------------------------------------------------------------------------

def gradual_deterioration(devices: dict) -> str:
    """Begin slowly escalating one device's heart rate toward cardiac arrest.

    Sets three private attributes on the chosen device. The simulator's tick
    loop detects these attributes and nudges ``_baseline_hr`` upward by
    ``_deterioration_rate`` bpm each tick for ``_deterioration_ticks`` ticks
    (default: 10 ticks ≈ 2.5 minutes at 15 s/tick). Gaussian noise from
    evolve() ensures the rise looks organic rather than stepwise.

    Args:
        devices: Mapping of device_id → DeviceState.

    Returns:
        The device_id of the deteriorating device.
    """
    target = random.choice(list(devices.values()))
    # Start from a mildly elevated baseline so the first few ticks look subtle
    target._baseline_hr          = max(target._baseline_hr, 90)
    target._deterioration_rate   = 9   # bpm per tick
    target._deterioration_ticks  = 10  # how many ticks to keep nudging
    return target.device_id


# ---------------------------------------------------------------------------
# Scenario 5 — Network Partition
# ---------------------------------------------------------------------------

def network_partition(devices: dict) -> list[str]:
    """Cut LoRa connectivity for all devices on one UAV relay for ~2 minutes.

    Selects all devices sharing a single UAV relay, saves their original RSSI
    baselines, then drops them to -125 dBm (well below the -100 poor-signal
    threshold). The simulator tick loop counts down ``_partition_ticks`` and
    restores the original baselines when the timer expires.

    Duration: 8 ticks × 15 s/tick = 2 minutes.

    Args:
        devices: Mapping of device_id → DeviceState.

    Returns:
        List of device_ids affected by the partition.
    """
    # Pick a relay at random and affect all devices behind it
    all_relays = list({dev.uav_relay_id for dev in devices.values()})
    target_relay = random.choice(all_relays)

    affected = []
    for dev in devices.values():
        if dev.uav_relay_id == target_relay:
            dev._pre_partition_rssi = dev._baseline_rssi
            dev._baseline_rssi      = -125
            dev._partition_ticks    = 8    # 8 × 15 s = 120 s ≈ 2 minutes
            affected.append(dev.device_id)

    return affected


# ---------------------------------------------------------------------------
# Dispatch table — maps scenario names from simulator_state.json
# ---------------------------------------------------------------------------

SCENARIO_REGISTRY: dict[str, callable] = {
    "sos_wave":             lambda devices, uavs: sos_wave(devices),
    "mass_casualty":        lambda devices, uavs: mass_casualty(devices),
    "uav_failure":          lambda devices, uavs: uav_failure(uavs),
    "gradual_deterioration": lambda devices, uavs: gradual_deterioration(devices),
    "network_partition":    lambda devices, uavs: network_partition(devices),
}
