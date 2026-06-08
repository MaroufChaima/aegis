"""
Assigns confidence scores to imputed sensor readings. A higher score means the
triage engine can rely more heavily on the value. Raw measured values always score
1.0. Imputed values are scored by method quality: forward fill > KNN > profile mean.
"""

from datetime import datetime


def assign_confidence_scores(
    enriched_readings: dict,
    sensor_statuses: dict,
    current_timestamp: str,
) -> dict:
    """Assigns confidence scores to all readings based on how the value was obtained.
    A raw measured value has confidence 1.0. Forward-filled values have confidence 0.85
    because the sensor recently provided a valid reading. KNN-imputed values have
    confidence 0.75 because similar victims provide reasonable estimates. Profile-mean
    values have confidence 0.60 because they use only the victims personal average
    without recent context. Unresolvable missing values have confidence 0.0 and the
    triage engine must account for this uncertainty."""

    if sensor_statuses is None:
        sensor_statuses = {}

    for sensor_type_id, entry in enriched_readings.items():
        method = entry.get("imputation_method")

        if method is None:
            entry["imputation_confidence"] = 1.0

        elif method == "forward_fill":
            confidence = 0.85
            if sensor_statuses.get(sensor_type_id) == "degraded":
                confidence -= 0.10
            entry["imputation_confidence"] = confidence

        elif method == "knn":
            entry["imputation_confidence"] = 0.75

        elif method == "profile_mean":
            entry["imputation_confidence"] = 0.60

        elif method in (
            "unresolvable",
            "not_imputable",
            "not_applicable",
            "no_history",
            "too_old",
            "skipped_damaged",
            "insufficient_neighbors",
        ):
            entry["imputation_confidence"] = 0.0

    return enriched_readings


def compute_packet_confidence(enriched_readings: dict) -> float:
    """Computes an overall confidence score for the entire packet as the mean of
    individual sensor confidence scores. Used to flag low-confidence packets for
    operator review."""

    scores = [
        entry["imputation_confidence"]
        for entry in enriched_readings.values()
        if entry.get("imputation_confidence") is not None
    ]

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 3)
