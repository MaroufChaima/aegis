"""
Manages one personalized IsolationForest anomaly detector per victim. Each detector
trains on that victim's own historical readings, enabling anomaly detection relative
to their personal physiological baseline rather than a population-level model.
"""

from sklearn.ensemble import IsolationForest
import numpy as np

# {victim_id: AnomalyDetectorInstance}. One detector per victim.
_registry: dict = {}

# {victim_id: list_of_feature_vectors}. Accumulates samples until cold start threshold is met.
_sample_buffers: dict = {}

# {victim_id: int}. Total samples seen since last retrain.
_sample_counts: dict = {}

COLD_START_THRESHOLD = 300
RETRAIN_EVERY        = 600


def _extract_features(readings_dict: dict) -> list:
    """Extracts a fixed-length feature vector from a readings dict for IsolationForest
    input. Uses only the four most clinically important vital signs. Missing values are
    replaced with 0.0 — this is intentional because the anomaly detector operates on
    raw sensor data before imputation."""

    return [
        readings_dict.get("heart_rate")     if readings_dict.get("heart_rate")     is not None else 0.0,
        readings_dict.get("temperature")    if readings_dict.get("temperature")    is not None else 0.0,
        readings_dict.get("spo2")           if readings_dict.get("spo2")           is not None else 0.0,
        readings_dict.get("respiratory_rate") if readings_dict.get("respiratory_rate") is not None else 0.0,
    ]


def predict(victim_id: str, readings_dict: dict) -> dict:
    """Returns anomaly detection result for one victim using their personal
    IsolationForest detector. During cold start (fewer than 300 samples) returns
    is_anomaly=False. After training, anomalies are detected based on deviation from
    this specific victims personal baseline patterns rather than a population-level
    model. Each victim has their own detector that trains on their own historical
    readings."""

    features = _extract_features(readings_dict)

    if victim_id not in _sample_buffers:
        _sample_buffers[victim_id] = []
    if victim_id not in _sample_counts:
        _sample_counts[victim_id] = 0

    _sample_buffers[victim_id].append(features)
    _sample_counts[victim_id] += 1

    total = _sample_counts[victim_id]

    if total < COLD_START_THRESHOLD:
        return {
            "is_anomaly":       False,
            "anomaly_score":    0.0,
            "confidence":       0.0,
            "detector_status":  "cold_start",
        }

    if total == COLD_START_THRESHOLD:
        clf = IsolationForest(contamination=0.1, random_state=42)
        clf.fit(np.array(_sample_buffers[victim_id]))
        _registry[victim_id] = clf
        print(f"[DETECTOR] Trained new detector for {victim_id} on {COLD_START_THRESHOLD} samples")

    if total % RETRAIN_EVERY == 0 and victim_id in _registry:
        recent = _sample_buffers[victim_id][-600:]
        clf = IsolationForest(contamination=0.1, random_state=42)
        clf.fit(np.array(recent))
        _registry[victim_id] = clf
        print(f"[DETECTOR] Retrained detector for {victim_id}")

    if victim_id in _registry:
        features_array = np.array([features])
        score      = _registry[victim_id].score_samples(features_array)[0]
        prediction = _registry[victim_id].predict(features_array)[0]
        is_anomaly = prediction == -1
        confidence = min(1.0, max(0.0, abs(score)))
        return {
            "is_anomaly":       bool(is_anomaly),
            "anomaly_score":    float(score),
            "confidence":       float(confidence),
            "detector_status":  "active",
        }

    return {
        "is_anomaly":       False,
        "anomaly_score":    0.0,
        "confidence":       0.0,
        "detector_status":  "cold_start",
    }


def get_detector_status(victim_id: str) -> dict:
    """Returns the current training status of the detector for a victim. Used for
    debugging and for the analytics page."""

    samples = _sample_counts.get(victim_id, 0)
    return {
        "victim_id":            victim_id,
        "samples_collected":    samples,
        "is_trained":           victim_id in _registry,
        "cold_start_remaining": max(0, COLD_START_THRESHOLD - samples),
    }
