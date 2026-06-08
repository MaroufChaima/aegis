"""
Assigns sensor types to all 15 victims based on their medical profile. All victims
receive the 12 standard sensors. Diabetic, cardiac, and neurological victims receive
one additional specialized sensor each. Safe to run multiple times — INSERT OR IGNORE
skips existing rows.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text
from datetime import datetime

NOW = datetime.utcnow().isoformat()

STANDARD_SENSORS = [
    "heart_rate",
    "spo2",
    "temperature",
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "respiratory_rate",
    "motion_activity",
    "fall_detected",
    "gps_lat",
    "gps_lon",
    "rssi",
    "battery",
]

SPECIALIZED_SENSORS = {
    "V-003": ["glucose"],
    "V-004": ["glucose"],
    "V-005": ["ecg_hr_variability"],
    "V-006": ["ecg_hr_variability"],
    "V-011": ["eeg_alert_index"],
}

VICTIM_IDS = [
    "V-001", "V-002", "V-003", "V-004", "V-005",
    "V-006", "V-007", "V-008", "V-009", "V-010",
    "V-011", "V-012", "V-013", "V-014", "V-015",
]


with engine.connect() as conn:
    for victim_id in VICTIM_IDS:
        all_sensors = STANDARD_SENSORS + SPECIALIZED_SENSORS.get(victim_id, [])
        for sensor_type_id in all_sensors:
            sensor_instance_id = f"{victim_id}-{sensor_type_id.upper().replace('_', '-')}-01"
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO victim_sensors "
                    "(victim_id, sensor_type_id, sensor_instance_id, is_active, failure_mode, assigned_at, notes) "
                    "VALUES (:victim_id, :sensor_type_id, :sensor_instance_id, :is_active, :failure_mode, :assigned_at, :notes)"
                ),
                {
                    "victim_id": victim_id,
                    "sensor_type_id": sensor_type_id,
                    "sensor_instance_id": sensor_instance_id,
                    "is_active": 1,
                    "failure_mode": None,
                    "assigned_at": NOW,
                    "notes": None,
                },
            )
    conn.commit()
    print("Victim sensors seeded.")
    rows = conn.execute(
        text("SELECT victim_id, COUNT(*) as sensor_count FROM victim_sensors GROUP BY victim_id ORDER BY victim_id")
    ).fetchall()
    for row in rows:
        print(f"{row[0]}: {row[1]} sensors")
