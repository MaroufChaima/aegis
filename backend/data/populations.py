"""
Generates per-region user populations, UAV fleet, and rescue teams.
Imported by demo_config.py, generate_demo.py, and mirrored in simulator/demo_config.py.
"""

import copy

REGIONS = {
    "algiers":     {"label": "Algiers",     "center": (36.7321, 3.0841),  "radius": 0.012, "alt_base": 15},
    "setif":       {"label": "Setif",       "center": (36.1911, 5.4137),  "radius": 0.010, "alt_base": 45},
    "bejaia":      {"label": "Bejaia",      "center": (36.7500, 5.0833),  "radius": 0.010, "alt_base": 12},
    "jijel":       {"label": "Jijel",       "center": (36.8206, 5.7667),  "radius": 0.010, "alt_base": 8},
    "constantine": {"label": "Constantine", "center": (36.3650, 6.6147),  "radius": 0.010, "alt_base": 38},
    "oran":        {"label": "Oran",        "center": (35.6969, -0.6331), "radius": 0.010, "alt_base": 18},
    "batna":       {"label": "Batna",       "center": (35.5559, 6.1742),  "radius": 0.010, "alt_base": 52},
}

DEFAULT_REGION = "algiers"

REGION_PREFIX = {
    "algiers": "ALG", "setif": "SET", "bejaia": "BJA", "jijel": "JIJ",
    "constantine": "CST", "oran": "ORN", "batna": "BAT",
}

# 8 users per region — covers all risk categories
REGION_USER_SPECS = [
    {"risk": "healthy",       "gender": "male",   "age": 34, "athlete": 0, "preg": 0, "conditions": "[]"},
    {"risk": "healthy",       "gender": "female", "age": 29, "athlete": 0, "preg": 0, "conditions": "[]"},
    {"risk": "diabetic",      "gender": "male",   "age": 48, "athlete": 0, "preg": 0, "conditions": '["diabetes"]'},
    {"risk": "cardiac",       "gender": "female", "age": 61, "athlete": 0, "preg": 0, "conditions": '["cardiovascular_disease"]'},
    {"risk": "elderly",       "gender": "male",   "age": 74, "athlete": 0, "preg": 0, "conditions": '["hypertension"]'},
    {"risk": "athlete",       "gender": "female", "age": 24, "athlete": 1, "preg": 0, "conditions": "[]"},
    {"risk": "neurological",  "gender": "male",   "age": 43, "athlete": 0, "preg": 0, "conditions": '["neurological_disorder"]'},
    {"risk": "child",         "gender": "male",   "age": 10, "athlete": 0, "preg": 0, "conditions": "[]"},
]

# Override last slot in algiers + constantine to pregnant
PREGNANT_REGIONS = {"algiers", "constantine"}

REGION_NAMES = {
    "algiers": [
        "Ahmed Benali", "Fatima Zahra", "Karim Messaoud", "Nadia Hamdi",
        "Youcef Amrani", "Samira Ouali", "Djamel Hadjadj", "Amina Khelifi",
    ],
    "setif": [
        "Hocine Boudiaf", "Yasmine Ferhat", "Mourad Zerrouki", "Salima Kaci",
        "Rachid Talbi", "Leila Boudjedra", "Farid Belhocine", "Bilal Ziani",
    ],
    "bejaia": [
        "Nassim Rahmani", "Ines Boualem", "Sofiane Harbi", "Meriem Saidi",
        "Hassan Benlazar", "Zohra Belkacem", "Omar Cherif", "Rym Dahmani",
    ],
    "jijel": [
        "Karim Bensaid", "Djamila Saidi", "Hocine Mokrani", "Lamia Touati",
        "Youcef Amrani", "Samira Ouali", "Djamel Hadjadj", "Bilal Ziani",
    ],
    "constantine": [
        "Mourad Zerrouki", "Fatima Zahra", "Karim Messaoud", "Nadia Hamdi",
        "Youcef Amrani", "Samira Ouali", "Djamel Hadjadj", "Amina Khelifi",
    ],
    "oran": [
        "Rachid Talbi", "Leila Boudjedra", "Hocine Boudiaf", "Yasmine Ferhat",
        "Farid Belhocine", "Ines Boualem", "Sofiane Harbi", "Bilal Ziani",
    ],
    "batna": [
        "Hassan Benlazar", "Zohra Belkacem", "Omar Cherif", "Meriem Saidi",
        "Nassim Rahmani", "Salima Kaci", "Mourad Zerrouki", "Bilal Ziani",
    ],
}

PROFILE_TEMPLATES = {
    "healthy": {
        "hr_baseline": 70, "hr_normal_min": 55, "hr_normal_max": 100,
        "spo2_normal_min": 95, "temp_normal_min": 36.1, "temp_normal_max": 37.5,
        "rr_normal_min": 12, "rr_normal_max": 20, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 90, "bp_systolic_normal_max": 130,
        "bp_diastolic_normal_min": 60, "bp_diastolic_normal_max": 85,
        "ecg_hrv_normal_min": 20, "ecg_hrv_normal_max": 80,
        "eeg_alert_index_normal_max": 0.3,
    },
    "diabetic": {
        "hr_baseline": 76, "hr_normal_min": 55, "hr_normal_max": 100,
        "spo2_normal_min": 94, "temp_normal_min": 36.1, "temp_normal_max": 37.5,
        "rr_normal_min": 12, "rr_normal_max": 20, "glucose_normal_min": 70, "glucose_normal_max": 140,
        "bp_systolic_normal_min": 90, "bp_systolic_normal_max": 135,
        "bp_diastolic_normal_min": 60, "bp_diastolic_normal_max": 88,
        "ecg_hrv_normal_min": 20, "ecg_hrv_normal_max": 80,
        "eeg_alert_index_normal_max": 0.3,
    },
    "cardiac": {
        "hr_baseline": 65, "hr_normal_min": 50, "hr_normal_max": 95,
        "spo2_normal_min": 93, "temp_normal_min": 36.0, "temp_normal_max": 37.5,
        "rr_normal_min": 12, "rr_normal_max": 22, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 85, "bp_systolic_normal_max": 140,
        "bp_diastolic_normal_min": 55, "bp_diastolic_normal_max": 90,
        "ecg_hrv_normal_min": 15, "ecg_hrv_normal_max": 60,
        "eeg_alert_index_normal_max": 0.3,
    },
    "elderly": {
        "hr_baseline": 68, "hr_normal_min": 50, "hr_normal_max": 90,
        "spo2_normal_min": 93, "temp_normal_min": 35.8, "temp_normal_max": 37.3,
        "rr_normal_min": 12, "rr_normal_max": 22, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 90, "bp_systolic_normal_max": 150,
        "bp_diastolic_normal_min": 60, "bp_diastolic_normal_max": 95,
        "ecg_hrv_normal_min": 15, "ecg_hrv_normal_max": 70,
        "eeg_alert_index_normal_max": 0.35,
    },
    "athlete": {
        "hr_baseline": 52, "hr_normal_min": 38, "hr_normal_max": 80,
        "spo2_normal_min": 96, "temp_normal_min": 36.2, "temp_normal_max": 37.4,
        "rr_normal_min": 10, "rr_normal_max": 18, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 85, "bp_systolic_normal_max": 125,
        "bp_diastolic_normal_min": 55, "bp_diastolic_normal_max": 80,
        "ecg_hrv_normal_min": 40, "ecg_hrv_normal_max": 120,
        "eeg_alert_index_normal_max": 0.25,
    },
    "neurological": {
        "hr_baseline": 72, "hr_normal_min": 55, "hr_normal_max": 100,
        "spo2_normal_min": 94, "temp_normal_min": 36.1, "temp_normal_max": 37.6,
        "rr_normal_min": 12, "rr_normal_max": 20, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 90, "bp_systolic_normal_max": 135,
        "bp_diastolic_normal_min": 60, "bp_diastolic_normal_max": 88,
        "ecg_hrv_normal_min": 20, "ecg_hrv_normal_max": 80,
        "eeg_alert_index_normal_max": 0.4,
    },
    "pregnant": {
        "hr_baseline": 80, "hr_normal_min": 60, "hr_normal_max": 105,
        "spo2_normal_min": 95, "temp_normal_min": 36.2, "temp_normal_max": 37.8,
        "rr_normal_min": 14, "rr_normal_max": 22, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 85, "bp_systolic_normal_max": 130,
        "bp_diastolic_normal_min": 55, "bp_diastolic_normal_max": 85,
        "ecg_hrv_normal_min": 20, "ecg_hrv_normal_max": 80,
        "eeg_alert_index_normal_max": 0.3,
    },
    "child": {
        "hr_baseline": 90, "hr_normal_min": 65, "hr_normal_max": 120,
        "spo2_normal_min": 96, "temp_normal_min": 36.3, "temp_normal_max": 38.0,
        "rr_normal_min": 18, "rr_normal_max": 30, "glucose_normal_min": None, "glucose_normal_max": None,
        "bp_systolic_normal_min": 80, "bp_systolic_normal_max": 110,
        "bp_diastolic_normal_min": 50, "bp_diastolic_normal_max": 70,
        "ecg_hrv_normal_min": 25, "ecg_hrv_normal_max": 90,
        "eeg_alert_index_normal_max": 0.35,
    },
}

STANDARD_SENSORS = [
    "heart_rate", "spo2", "temperature", "blood_pressure_systolic",
    "blood_pressure_diastolic", "respiratory_rate", "motion_activity",
    "fall_detected", "gps_lat", "gps_lon", "altitude_m", "rssi", "battery",
]

SENSOR_EXTRAS = {
    "diabetic": ["glucose"],
    "cardiac": ["ecg_hr_variability"],
    "neurological": ["eeg_alert_index"],
}

ANTHRO = [
    (178, 82), (165, 62), (172, 88), (160, 74), (170, 78),
    (168, 58), (176, 85), (135, 32),
]


def _user_id(region_key: str, index: int) -> str:
    return f"{REGION_PREFIX[region_key]}-U-{index + 1:02d}"


def _uav_id(region_key: str, index: int) -> str:
    label = REGIONS[region_key]["label"]
    return f"{label}-UAV-{index + 1:02d}"


def build_populations():
    users = []
    profiles = []
    sensor_assignments = []
    uav_ids = []
    uav_names = {}

    for region_key in REGIONS:
        names = REGION_NAMES[region_key]
        for i, spec in enumerate(REGION_USER_SPECS):
            risk = spec["risk"]
            if i == 7 and region_key in PREGNANT_REGIONS:
                risk = "pregnant"
                spec = {**spec, "risk": "pregnant", "gender": "female", "age": 31, "preg": 1}

            uid = _user_id(region_key, i)
            h, w = ANTHRO[i % len(ANTHRO)]
            users.append({
                "victim_id": uid,
                "name": names[i],
                "age": spec["age"],
                "gender": spec["gender"],
                "medical_conditions": spec["conditions"],
                "risk_category": risk,
                "pregnancy_status": spec["preg"],
                "is_athlete": spec["athlete"],
                "height_cm": h,
                "weight_kg": w,
                "home_region": region_key,
                "notes": f"{risk.title()} profile — {REGIONS[region_key]['label']}",
            })

            tmpl = copy.deepcopy(PROFILE_TEMPLATES[risk])
            profiles.append({
                "victim_id": uid,
                **tmpl,
                "notes": f"Personalized {risk} thresholds for {names[i]}",
            })

            sensors = list(STANDARD_SENSORS)
            sensors.extend(SENSOR_EXTRAS.get(risk, []))
            for st in sensors:
                sensor_assignments.append({"victim_id": uid, "sensor_type_id": st})

        for j in range(5):
            uav_id = _uav_id(region_key, j)
            uav_ids.append(uav_id)
            uav_names[uav_id] = uav_id

    return users, profiles, sensor_assignments, uav_ids, uav_names


USERS, PROFILES, SENSOR_ASSIGNMENTS, ALL_UAV_IDS, UAV_NAMES = build_populations()

VICTIM_UAV_MAP = {}  # filled dynamically by assignment service / simulator

RESCUE_TEAMS = []
RESCUERS = []
TEAM_VICTIM_ASSIGNMENTS = {}
TEAM_UAV_ASSIGNMENTS = {}

_TEAM_DEFS = [
    ("civil_protection", "Protection Civile — Wilaya de {label}", "Active"),
    ("firefighters", "Sapeurs-Pompiers — {label}", "Active"),
    ("medical", "SAMU / EMS — {label}", "Standby"),
    ("search_rescue", "Unité de Secours — {label}", "Standby"),
]

_rescuer_counter = 1
for region_key, region in REGIONS.items():
    prefix = REGION_PREFIX[region_key]
    lat, lon = region["center"]
    region_users = [u["victim_id"] for u in USERS if u["home_region"] == region_key]
    region_uavs = [_uav_id(region_key, j) for j in range(5)]

    for ti, (team_type, name_tpl, status) in enumerate(_TEAM_DEFS):
        tid = f"RT-{prefix}-{ti + 1:02d}"
        RESCUE_TEAMS.append({
            "team_id": tid,
            "team_name": name_tpl.format(label=region["label"]),
            "team_type": team_type,
            "specialization": team_type,
            "current_region": region_key,
            "status": status,
            "latitude": lat + 0.003 * (ti + 1),
            "longitude": lon + 0.003 * (ti + 1),
        })
        TEAM_VICTIM_ASSIGNMENTS[tid] = region_users[ti * 2:(ti + 1) * 2] or region_users[:2]
        if ti < len(region_uavs):
            TEAM_UAV_ASSIGNMENTS.setdefault(tid, []).append(region_uavs[ti])

        for role in ("medic", "paramedic", "coordinator"):
            rid = f"R-{prefix}-{_rescuer_counter:03d}"
            _rescuer_counter += 1
            RESCUERS.append({
                "rescuer_id": rid,
                "team_id": tid,
                "first_name": ["Karim", "Salima", "Nassim"][_rescuer_counter % 3],
                "last_name": ["Bensaid", "Kaci", "Rahmani"][_rescuer_counter % 3],
                "role": role,
                "age": 30 + (_rescuer_counter % 15),
                "phone": f"+213-555-{_rescuer_counter:04d}",
                "years_experience": 4 + (_rescuer_counter % 10),
            })

VICTIM_EXTRA = {u["victim_id"]: {
    "height_cm": u["height_cm"], "weight_kg": u["weight_kg"], "home_region": u["home_region"],
} for u in USERS}
