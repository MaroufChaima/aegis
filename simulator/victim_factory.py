"""Dynamic victim factory — builds users for one region from populations."""

from physiological_profile import PhysiologicalProfile
from victim_wban import VictimWBAN
from demo_config import users_for_region, profile_for_user, sensors_for_user


def create_victims_for_region(region_key: str) -> list:
    victims = []
    for user in users_for_region(region_key):
        prof = profile_for_user(user["victim_id"])
        profile = PhysiologicalProfile(
            victim_id=user["victim_id"],
            risk_category=user["risk_category"],
            region_key=region_key,
            hr_baseline=float(prof["hr_baseline"]),
            hr_normal_min=float(prof["hr_normal_min"]),
            hr_normal_max=float(prof["hr_normal_max"]),
            temp_normal_min=float(prof["temp_normal_min"]),
            temp_normal_max=float(prof["temp_normal_max"]),
            spo2_normal_min=float(prof["spo2_normal_min"]),
            rr_normal_min=float(prof["rr_normal_min"]),
            rr_normal_max=float(prof["rr_normal_max"]),
            glucose_normal_min=prof.get("glucose_normal_min"),
            glucose_normal_max=prof.get("glucose_normal_max"),
            bp_systolic_normal_min=float(prof["bp_systolic_normal_min"]),
            bp_systolic_normal_max=float(prof["bp_systolic_normal_max"]),
        )
        victim = VictimWBAN(
            victim_id=user["victim_id"],
            name=user["name"],
            risk_category=user["risk_category"],
            uav_relay_id=None,
            sensor_type_ids=sensors_for_user(user["victim_id"]),
            profile=profile,
            height_cm=user.get("height_cm"),
            weight_kg=user.get("weight_kg"),
            home_region=region_key,
        )
        victims.append(victim)
    return victims


def create_all_victims(region_key: str) -> list:
    return create_victims_for_region(region_key)
