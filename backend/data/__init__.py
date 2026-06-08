"""
Seed data scripts for AEGIS WBAN architecture. Run these scripts in this exact order
before starting the simulator: 1. seed_sensor_types.py, 2. seed_victims.py,
3. seed_profiles.py, 4. seed_victim_sensors.py. Each script is safe to run multiple
times — it uses INSERT OR IGNORE to skip rows that already exist.
"""
