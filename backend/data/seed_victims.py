"""
Seeds 15 victims into the victims table.
Run from backend/: python data/seed_victims.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text
from datetime import datetime
from data.demo_config import VICTIM_EXTRA

NOW = datetime.utcnow().isoformat()

VICTIMS = [
    {
        "victim_id": "V-001",
        "name": "Ahmed Benali",
        "age": 34,
        "gender": "male",
        "medical_conditions": "[]",
        "risk_category": "healthy",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Healthy adult male baseline profile",
    },
    {
        "victim_id": "V-002",
        "name": "Fatima Zahra",
        "age": 28,
        "gender": "female",
        "medical_conditions": "[]",
        "risk_category": "healthy",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Healthy adult female baseline profile",
    },
    {
        "victim_id": "V-003",
        "name": "Karim Messaoud",
        "age": 42,
        "gender": "male",
        "medical_conditions": '["diabetes"]',
        "risk_category": "diabetic",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Type 2 diabetic — glucose sensor assigned",
    },
    {
        "victim_id": "V-004",
        "name": "Nadia Hamdi",
        "age": 55,
        "gender": "female",
        "medical_conditions": '["diabetes", "hypertension"]',
        "risk_category": "diabetic",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Diabetic with hypertension — glucose sensor assigned, elevated BP thresholds",
    },
    {
        "victim_id": "V-005",
        "name": "Omar Cherif",
        "age": 61,
        "gender": "male",
        "medical_conditions": '["cardiovascular_disease"]',
        "risk_category": "cardiac",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Cardiac patient — ECG sensor assigned",
    },
    {
        "victim_id": "V-006",
        "name": "Leila Boudjedra",
        "age": 58,
        "gender": "female",
        "medical_conditions": '["cardiovascular_disease", "hypertension"]',
        "risk_category": "cardiac",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Cardiac patient with hypertension — ECG sensor assigned",
    },
    {
        "victim_id": "V-007",
        "name": "Youcef Amrani",
        "age": 72,
        "gender": "male",
        "medical_conditions": "[]",
        "risk_category": "elderly",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Elderly male — different cardiovascular response expected",
    },
    {
        "victim_id": "V-008",
        "name": "Zohra Belkacem",
        "age": 68,
        "gender": "female",
        "medical_conditions": '["hypertension"]',
        "risk_category": "elderly",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Elderly female with hypertension",
    },
    {
        "victim_id": "V-009",
        "name": "Rachid Talbi",
        "age": 26,
        "gender": "male",
        "medical_conditions": "[]",
        "risk_category": "athlete",
        "pregnancy_status": 0,
        "is_athlete": 1,
        "notes": "Competitive athlete — naturally lower resting heart rate is normal",
    },
    {
        "victim_id": "V-010",
        "name": "Samira Ouali",
        "age": 23,
        "gender": "female",
        "medical_conditions": "[]",
        "risk_category": "athlete",
        "pregnancy_status": 0,
        "is_athlete": 1,
        "notes": "Competitive athlete — lower resting HR and different cardiovascular response",
    },
    {
        "victim_id": "V-011",
        "name": "Djamel Hadjadj",
        "age": 45,
        "gender": "male",
        "medical_conditions": '["neurological_disorder"]',
        "risk_category": "neurological",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Neurological patient — EEG sensor assigned",
    },
    {
        "victim_id": "V-012",
        "name": "Amina Khelifi",
        "age": 31,
        "gender": "female",
        "medical_conditions": "[]",
        "risk_category": "pregnant",
        "pregnancy_status": 1,
        "is_athlete": 0,
        "notes": "Pregnant — altered cardiovascular and respiratory parameters expected",
    },
    {
        "victim_id": "V-013",
        "name": "Hassan Benlazar",
        "age": 38,
        "gender": "male",
        "medical_conditions": "[]",
        "risk_category": "healthy",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Healthy adult male",
    },
    {
        "victim_id": "V-014",
        "name": "Meriem Saidi",
        "age": 44,
        "gender": "female",
        "medical_conditions": "[]",
        "risk_category": "healthy",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Healthy adult female",
    },
    {
        "victim_id": "V-015",
        "name": "Bilal Ziani",
        "age": 9,
        "gender": "male",
        "medical_conditions": "[]",
        "risk_category": "child",
        "pregnancy_status": 0,
        "is_athlete": 0,
        "notes": "Child — naturally higher heart rate and slightly elevated temperature normal",
    },
]


def seed():
    with engine.connect() as conn:
        for victim in VICTIMS:
            extra = VICTIM_EXTRA.get(victim["victim_id"], {})
            victim = {**victim, **extra, "created_at": NOW}
            conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO victims
                    (victim_id, name, age, gender, medical_conditions, risk_category,
                     pregnancy_status, is_athlete, notes, created_at,
                     height_cm, weight_kg, home_region)
                    VALUES
                    (:victim_id, :name, :age, :gender, :medical_conditions, :risk_category,
                     :pregnancy_status, :is_athlete, :notes, :created_at,
                     :height_cm, :weight_kg, :home_region)
                    """
                ),
                victim,
            )
        conn.commit()
        result = conn.execute(text("SELECT COUNT(*) FROM victims"))
        print(f"Victims seeded. Total rows: {result.scalar()}")


if __name__ == "__main__":
    seed()
