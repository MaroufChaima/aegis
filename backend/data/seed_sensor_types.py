"""
Seeds the sensor_types reference table with all supported sensor types for the AEGIS
WBAN architecture. Safe to run multiple times — INSERT OR IGNORE skips existing rows.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text


SENSOR_TYPES = [
    # Standard sensors
    {
        "sensor_type_id": "heart_rate",
        "display_name": "Heart Rate Monitor",
        "unit": "bpm",
        "category": "standard",
        "normal_min_global": 40.0,
        "normal_max_global": 200.0,
        "is_critical": 1,
        "description": "Beats per minute measured by optical or ECG sensor",
    },
    {
        "sensor_type_id": "spo2",
        "display_name": "Pulse Oximeter",
        "unit": "%",
        "category": "standard",
        "normal_min_global": 90.0,
        "normal_max_global": 100.0,
        "is_critical": 1,
        "description": "Blood oxygen saturation percentage",
    },
    {
        "sensor_type_id": "temperature",
        "display_name": "Body Temperature Sensor",
        "unit": "Celsius",
        "category": "standard",
        "normal_min_global": 35.0,
        "normal_max_global": 40.0,
        "is_critical": 1,
        "description": "Core body temperature",
    },
    {
        "sensor_type_id": "blood_pressure_systolic",
        "display_name": "Blood Pressure Systolic",
        "unit": "mmHg",
        "category": "standard",
        "normal_min_global": 80.0,
        "normal_max_global": 140.0,
        "is_critical": 0,
        "description": "Systolic blood pressure upper value",
    },
    {
        "sensor_type_id": "blood_pressure_diastolic",
        "display_name": "Blood Pressure Diastolic",
        "unit": "mmHg",
        "category": "standard",
        "normal_min_global": 50.0,
        "normal_max_global": 90.0,
        "is_critical": 0,
        "description": "Diastolic blood pressure lower value",
    },
    {
        "sensor_type_id": "respiratory_rate",
        "display_name": "Respiratory Rate Monitor",
        "unit": "breaths/min",
        "category": "standard",
        "normal_min_global": 8.0,
        "normal_max_global": 25.0,
        "is_critical": 1,
        "description": "Breathing rate per minute",
    },
    {
        "sensor_type_id": "motion_activity",
        "display_name": "Motion Activity Sensor",
        "unit": "score 0-1",
        "category": "standard",
        "normal_min_global": 0.0,
        "normal_max_global": 1.0,
        "is_critical": 0,
        "description": "Activity level from 0.0 (no movement) to 1.0 (high activity)",
    },
    {
        "sensor_type_id": "fall_detected",
        "display_name": "Fall Detection Sensor",
        "unit": "boolean",
        "category": "standard",
        "normal_min_global": 0.0,
        "normal_max_global": 0.0,
        "is_critical": 1,
        "description": "1 if a fall was detected this reading period, 0 otherwise",
    },
    {
        "sensor_type_id": "gps_lat",
        "display_name": "GPS Latitude",
        "unit": "degrees",
        "category": "standard",
        "normal_min_global": -90.0,
        "normal_max_global": 90.0,
        "is_critical": 0,
        "description": "WGS84 latitude coordinate",
    },
    {
        "sensor_type_id": "gps_lon",
        "display_name": "GPS Longitude",
        "unit": "degrees",
        "category": "standard",
        "normal_min_global": -180.0,
        "normal_max_global": 180.0,
        "is_critical": 0,
        "description": "WGS84 longitude coordinate",
    },
    # Specialized sensors
    {
        "sensor_type_id": "glucose",
        "display_name": "Glucose Sensor",
        "unit": "mg/dL",
        "category": "specialized",
        "normal_min_global": 70.0,
        "normal_max_global": 180.0,
        "is_critical": 1,
        "description": "Blood glucose level. Assigned only to diabetic victims",
    },
    {
        "sensor_type_id": "ecg_hr_variability",
        "display_name": "ECG Heart Rate Variability",
        "unit": "ms",
        "category": "specialized",
        "normal_min_global": 20.0,
        "normal_max_global": 100.0,
        "is_critical": 1,
        "description": "Heart rate variability measured by ECG. Assigned only to cardiac victims",
    },
    {
        "sensor_type_id": "eeg_alert_index",
        "display_name": "EEG Alert Index",
        "unit": "index 0-100",
        "category": "specialized",
        "normal_min_global": 0.0,
        "normal_max_global": 100.0,
        "is_critical": 0,
        "description": "Neurological alertness index from EEG. Assigned only to neurological victims",
    },
    {
        "sensor_type_id": "rssi",
        "display_name": "Signal Strength",
        "unit": "dBm",
        "category": "standard",
        "normal_min_global": -120.0,
        "normal_max_global": 0.0,
        "is_critical": 0,
        "description": "Received signal strength indicator for the WBAN coordinator",
    },
    {
        "sensor_type_id": "battery",
        "display_name": "Battery Level",
        "unit": "%",
        "category": "standard",
        "normal_min_global": 0.0,
        "normal_max_global": 100.0,
        "is_critical": 0,
        "description": "Coordinator node battery percentage",
    },
]


with engine.connect() as conn:
    for sensor_type in SENSOR_TYPES:
        conn.execute(
            text(
                "INSERT OR IGNORE INTO sensor_types "
                "(sensor_type_id, display_name, unit, category, normal_min_global, normal_max_global, is_critical, description) "
                "VALUES (:sensor_type_id, :display_name, :unit, :category, :normal_min_global, :normal_max_global, :is_critical, :description)"
            ),
            sensor_type,
        )
    conn.commit()
    print("Sensor types seeded. Total rows in sensor_types table:")
    result = conn.execute(text("SELECT COUNT(*) FROM sensor_types"))
    print(result.scalar())
