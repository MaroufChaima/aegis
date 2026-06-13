"""Re-exports canonical demo data from populations.py."""

from data.populations import (
    REGIONS, DEFAULT_REGION, REGION_PREFIX,
    USERS, PROFILES, SENSOR_ASSIGNMENTS,
    ALL_UAV_IDS, UAV_NAMES, VICTIM_EXTRA,
    RESCUE_TEAMS, RESCUERS, TEAM_VICTIM_ASSIGNMENTS, TEAM_UAV_ASSIGNMENTS,
    STANDARD_SENSORS, SENSOR_EXTRAS, PROFILE_TEMPLATES,
    _uav_id, _user_id,
)

# Backward compat aliases
VICTIM_UAV_MAP = {}
