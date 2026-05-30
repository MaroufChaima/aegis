"""
Static configuration for the AEGIS simulator.
All tuneable values live here so simulator.py and device_model.py
never contain magic numbers.
"""

# Wearable device identifiers — 15 virtual field operatives
DEVICE_IDS = [f"WB-{i:03d}" for i in range(1, 16)]

# UAV relay identifiers — 4 aerial gateways covering the zone
UAV_IDS = ["UAV-01", "UAV-02", "UAV-03", "UAV-04"]

# Seconds between each simulator tick (one POST per device per tick)
EMIT_INTERVAL = 15

# FastAPI backend base URL
API_URL = "http://localhost:8000"

# Geographic centre of the simulated disaster zone (Algiers region)
# All devices spawn within ZONE_RADIUS_DEG degrees of this point
ZONE_CENTER = (36.7321, 3.0841)
ZONE_RADIUS_DEG = 0.02        # roughly 2 km radius at this latitude
