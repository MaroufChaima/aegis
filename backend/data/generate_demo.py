"""
One-shot demo data generator for the full multi-region AEGIS population.
Run from backend/: python data/generate_demo.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine
from data.populations import (
    REGIONS, DEFAULT_REGION, USERS, PROFILES, SENSOR_ASSIGNMENTS,
    ALL_UAV_IDS, UAV_NAMES, RESCUE_TEAMS, RESCUERS,
    TEAM_VICTIM_ASSIGNMENTS, TEAM_UAV_ASSIGNMENTS, _uav_id,
)

NOW = datetime.utcnow().isoformat()


def main():
    from migrations.apply_schema_updates import main as m1
    from migrations.apply_region_redesign import main as m2
    m1()
    m2()

    with engine.connect() as conn:
        # Clear operational state for fresh demo
        for table in (
            "victim_current_state", "team_victim_assignments", "team_uav_assignments",
            "telemetry_readings", "coordinator_packets", "alerts",
        ):
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass

        for user in USERS:
            conn.execute(
                text("""
                    INSERT OR REPLACE INTO victims
                    (victim_id, name, age, gender, medical_conditions, risk_category,
                     pregnancy_status, is_athlete, notes, created_at,
                     height_cm, weight_kg, home_region)
                    VALUES
                    (:victim_id, :name, :age, :gender, :medical_conditions, :risk_category,
                     :pregnancy_status, :is_athlete, :notes, :created_at,
                     :height_cm, :weight_kg, :home_region)
                """),
                {**user, "created_at": NOW},
            )

        for profile in PROFILES:
            conn.execute(
                text("""
                    INSERT OR REPLACE INTO victim_physiological_profiles
                    (victim_id, hr_baseline, hr_normal_min, hr_normal_max, spo2_normal_min,
                     temp_normal_min, temp_normal_max, rr_normal_min, rr_normal_max,
                     glucose_normal_min, glucose_normal_max,
                     bp_systolic_normal_min, bp_systolic_normal_max, notes, updated_at)
                    VALUES
                    (:victim_id, :hr_baseline, :hr_normal_min, :hr_normal_max, :spo2_normal_min,
                     :temp_normal_min, :temp_normal_max, :rr_normal_min, :rr_normal_max,
                     :glucose_normal_min, :glucose_normal_max,
                     :bp_systolic_normal_min, :bp_systolic_normal_max, :notes, :updated_at)
                """),
                {**profile, "updated_at": NOW},
            )

        conn.execute(text("DELETE FROM victim_sensors"))
        for sa in SENSOR_ASSIGNMENTS:
            conn.execute(
                text("""
                    INSERT INTO victim_sensors (victim_id, sensor_type_id, sensor_instance_id, is_active)
                    VALUES (:victim_id, :sensor_type_id, :inst, 1)
                """),
                {
                    "victim_id": sa["victim_id"],
                    "sensor_type_id": sa["sensor_type_id"],
                    "inst": f"{sa['victim_id']}-{sa['sensor_type_id'].upper()}-01",
                },
            )

        for team in RESCUE_TEAMS:
            conn.execute(
                text("""
                    INSERT OR REPLACE INTO rescue_teams
                    (team_id, team_name, team_type, specialization, current_region, status, latitude, longitude)
                    VALUES
                    (:team_id, :team_name, :team_type, :specialization, :current_region, :status, :latitude, :longitude)
                """),
                team,
            )

        for rescuer in RESCUERS:
            conn.execute(
                text("""
                    INSERT OR REPLACE INTO rescuers
                    (rescuer_id, team_id, first_name, last_name, role, age, phone, years_experience)
                    VALUES
                    (:rescuer_id, :team_id, :first_name, :last_name, :role, :age, :phone, :years_experience)
                """),
                rescuer,
            )

        conn.execute(text("DELETE FROM team_victim_assignments"))
        for team_id, victim_ids in TEAM_VICTIM_ASSIGNMENTS.items():
            for vid in victim_ids:
                conn.execute(
                    text("""
                        INSERT INTO team_victim_assignments (team_id, victim_id, assigned_at)
                        VALUES (:team_id, :victim_id, :assigned_at)
                    """),
                    {"team_id": team_id, "victim_id": vid, "assigned_at": NOW},
                )

        conn.execute(text("DELETE FROM team_uav_assignments"))
        for team_id, uav_ids in TEAM_UAV_ASSIGNMENTS.items():
            for uid in uav_ids:
                conn.execute(
                    text("""
                        INSERT INTO team_uav_assignments (team_id, uav_id, assigned_at)
                        VALUES (:team_id, :uav_id, :assigned_at)
                    """),
                    {"team_id": team_id, "uav_id": uid, "assigned_at": NOW},
                )

        conn.execute(text("DELETE FROM uav_positions"))
        for region_key, region in REGIONS.items():
            lat, lon = region["center"]
            for j in range(5):
                uav_id = _uav_id(region_key, j)
                conn.execute(
                    text("""
                        INSERT INTO uav_positions
                        (uav_id, name, home_region, current_region, timestamp, latitude, longitude,
                         altitude, battery, status, coverage_radius, connected_devices)
                        VALUES
                        (:uav_id, :name, :home_region, :current_region, :timestamp, :latitude, :longitude,
                         :altitude, :battery, :status, :coverage_radius, :connected_devices)
                    """),
                    {
                        "uav_id": uav_id,
                        "name": uav_id,
                        "home_region": region_key,
                        "current_region": region_key,
                        "timestamp": NOW,
                        "latitude": lat + 0.002 * (j + 1),
                        "longitude": lon + 0.002 * (j + 1),
                        "altitude": 120.0,
                        "battery": 85,
                        "status": "standby",
                        "coverage_radius": 800.0,
                        "connected_devices": 0,
                    },
                )

        conn.commit()

    print(f"Demo data generated: {len(USERS)} users, {len(ALL_UAV_IDS)} UAVs, {len(RESCUE_TEAMS)} teams")


if __name__ == "__main__":
    main()
