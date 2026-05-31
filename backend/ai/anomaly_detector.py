"""
Isolation Forest anomaly detector for the AEGIS AI pipeline.

Detects statistically unusual vital-sign patterns that may not breach
any single rule threshold — the complement to the rule-based triage scorer.
No database access, no side effects outside the instance's own state.
"""

import logging

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_SAMPLES      = 300   # cold-start: return no-anomaly until buffer reaches this size
RETRAIN_INTERVAL = 600   # retrain the model every N new samples after first training
BUFFER_CAP       = 2000  # maximum buffer size — older samples are dropped when exceeded
CONTAMINATION    = 0.05  # fraction of training data expected to be anomalous (~5%)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _extract_features(record: dict) -> list[float]:
    """Extract the 5-element feature vector used for training and inference.

    GPS coordinates are excluded because their systematic drift would confuse
    the anomaly detector. SOS signal is excluded because it is handled by the
    rule-based scorer. Timestamp is excluded to make detection
    location-and-time independent.

    Args:
        record: Dict containing at minimum heart_rate, temperature, movement,
                rssi, and battery keys.

    Returns:
        List of five floats: [heart_rate, temperature, movement, rssi, battery].
    """
    return [
        float(record["heart_rate"]),
        float(record["temperature"]),
        float(record.get("movement", 1)),
        float(record["rssi"]),
        float(record["battery"]),
    ]


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Wraps scikit-learn IsolationForest for streaming telemetry anomaly detection.

    Lifecycle
    ---------
    1. **Cold start** — buffer accumulates telemetry until ``MIN_SAMPLES`` records
       are available. Every ``predict()`` call during this phase returns
       ``is_anomaly=False`` with zero scores.
    2. **First training** — triggered automatically when the buffer hits
       ``MIN_SAMPLES``. StandardScaler fits on the buffer, then IsolationForest
       trains on the scaled data.
    3. **Inference** — subsequent ``predict()`` calls scale the incoming record
       and run IsolationForest inference in sub-millisecond time.
    4. **Periodic retraining** — every ``RETRAIN_INTERVAL`` samples after the
       first training, the model retrains on the most recent ``BUFFER_CAP``
       records, adapting to gradual drift in the population's baseline vitals.

    Why IsolationForest?
    --------------------
    - Unsupervised: requires no labelled anomalous training examples.
    - Works on tabular feature vectors, not raw time series.
    - Sub-millisecond inference — negligible latency on the ingest path.
    - Continuous anomaly score enables confidence-threshold filtering in the
      alert generator, reducing noisy alerts.

    Thread safety
    -------------
    Not thread-safe. For the prototype's single-process uvicorn deployment
    this is not an issue. A future async retraining task should use a lock.
    """

    def __init__(self) -> None:
        self._buffer: list[list[float]] = []
        self._model: IsolationForest | None = None
        self._scaler: StandardScaler | None = None
        self._is_trained: bool = False
        self._samples_since_retrain: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_sample(self, record: dict) -> None:
        """Append one telemetry record to the training buffer.

        Call this for every validated packet regardless of whether the model
        is trained. The buffer is capped at ``BUFFER_CAP`` entries — when the
        cap is reached, the oldest entries are discarded so the model can
        adapt to population drift over the course of a long simulation.

        This method does NOT trigger training or inference. Call ``predict()``
        for combined add-and-predict behaviour.

        Args:
            record: Telemetry dict containing at minimum the five feature keys.
        """
        self._buffer.append(_extract_features(record))
        if len(self._buffer) > BUFFER_CAP:
            self._buffer = self._buffer[-BUFFER_CAP:]

    def predict(self, record: dict) -> dict:
        """Add a sample to the buffer and return an anomaly prediction.

        Combines ``add_sample()`` and inference into one call for convenience
        on the ingest path. Training and retraining are triggered automatically
        based on buffer size and sample count.

        Cold-start behaviour
        ~~~~~~~~~~~~~~~~~~~~
        Until ``MIN_SAMPLES`` records have been buffered the model cannot
        distinguish normal from abnormal. During this phase every call returns
        ``is_anomaly=False, anomaly_score=0.0, confidence=0.0`` so downstream
        alert logic is not flooded with meaningless flags.

        Confidence mapping
        ~~~~~~~~~~~~~~~~~~
        IsolationForest's ``score_samples()`` returns a raw anomaly score in
        roughly the range [-0.5, +0.5]. More negative = more anomalous.
        For anomalous predictions, confidence is mapped to [0, 1] by dividing
        ``|raw_score|`` by 0.5 (the approximate worst-case magnitude) and
        clamping. Normal predictions always return confidence=0.0 — the alert
        generator only acts on ``is_anomaly=True`` readings anyway.

        Args:
            record: Telemetry dict for the current packet.

        Returns:
            Dict with three keys:
                is_anomaly (bool)     — True if the model predicts an anomaly
                anomaly_score (float) — raw IsolationForest score; more negative
                                        means more anomalous
                confidence (float)    — 0.0–1.0; useful for alert thresholding
        """
        self.add_sample(record)
        self._samples_since_retrain += 1

        # Cold start — not enough data to train
        if len(self._buffer) < MIN_SAMPLES:
            remaining = MIN_SAMPLES - len(self._buffer)
            log.debug("AnomalyDetector cold start: %d samples remaining", remaining)
            return {"is_anomaly": False, "anomaly_score": 0.0, "confidence": 0.0}

        # First training trigger
        if not self._is_trained:
            self._train()

        # Periodic retraining
        if self._samples_since_retrain >= RETRAIN_INTERVAL:
            self._train()

        # Inference
        features = np.array([_extract_features(record)])
        features_scaled = self._scaler.transform(features)

        raw_score  = float(self._model.score_samples(features_scaled)[0])
        prediction = int(self._model.predict(features_scaled)[0])  # -1=anomaly, 1=normal

        is_anomaly = prediction == -1
        confidence = min(abs(raw_score) / 0.5, 1.0) if is_anomaly else 0.0

        return {
            "is_anomaly":    is_anomaly,
            "anomaly_score": raw_score,
            "confidence":    float(confidence),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _train(self) -> None:
        """Fit the scaler and IsolationForest on the current buffer.

        Uses ``random_state=42`` for reproducibility — identical buffer
        contents always produce the same model, which simplifies debugging
        and thesis evaluation.

        Sets ``_is_trained=True`` and resets ``_samples_since_retrain``
        so the retraining countdown restarts from zero.
        """
        X = np.array(self._buffer)

        self._scaler = StandardScaler()
        X_scaled = self._scaler.fit_transform(X)

        self._model = IsolationForest(
            n_estimators=100,
            contamination=CONTAMINATION,
            random_state=42,
        )
        self._model.fit(X_scaled)

        self._is_trained = True
        self._samples_since_retrain = 0
        log.info(
            "AnomalyDetector trained on %d samples (buffer=%d)",
            len(self._buffer),
            len(self._buffer),
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

detector = AnomalyDetector()
"""Shared AnomalyDetector instance.

Import this singleton in the ingest pipeline so model state (buffer,
trained weights) persists across requests for the lifetime of the uvicorn
process. Creating a new instance per request would reset the buffer and
prevent the model from ever training.

Usage::

    from ai.anomaly_detector import detector

    result = detector.predict(telemetry_data)
"""
