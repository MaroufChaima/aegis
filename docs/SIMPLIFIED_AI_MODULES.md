# SIMPLIFIED_AI_MODULES.md — AI/ML Implementation Guide

> This document specifies the AI modules for the AEGIS prototype. Each module is academically credible, implementable with scikit-learn in a few dozen lines of Python, and designed to be comparable and evaluatable for thesis experiments.

---

## Overview: the hybrid AI approach

The prototype uses a **hybrid rule-based + machine learning** approach. This is not a simplification — it is actually a well-established and academically interesting design choice.

**Why hybrid?**

| Concern | Rule-based | Machine Learning |
|---|---|---|
| Speed | Instant — zero computation | Fast, but requires model inference |
| Transparency | Fully explainable | Black box (partially) |
| Coverage | Only catches known patterns | Can detect novel anomalies |
| Data requirements | None | Needs training data |
| Tuning | Manual threshold adjustment | Contamination + feature selection |

By combining both, you get **speed + coverage**. Rules catch obvious emergencies (HR=30) in microseconds. The ML model catches subtle patterns that don't trigger any individual rule threshold. Your thesis can compare the two approaches, which gives you an evaluation experiment with clear results.

**Academic framing**: 
> "The system employs a hybrid intelligence architecture combining a deterministic rule engine with an unsupervised machine learning anomaly detector. The rule engine provides transparent, always-explainable decisions for threshold breaches, while the Isolation Forest detects multivariate anomalies that fall outside normal vital patterns but may not breach any single threshold. This design is consistent with the principle of human-interpretable AI in safety-critical systems."

---

## Module 1 — Rule-based triage scorer

**File**: `backend/ai/triage_scorer.py`

**Algorithm**: Weighted additive scoring with priority classification

**What it does**: Takes a single telemetry reading and assigns a severity score from 0 to 100, then classifies into P1 (critical), P2 (urgent), or P3 (stable).

### Scoring weights

| Condition | Points | Clinical rationale |
|---|---|---|
| SOS signal active | +50 | Explicit distress call |
| Heart rate < 40 bpm | +40 | Severe bradycardia, potentially cardiac arrest |
| Heart rate > 150 bpm | +20 | Severe tachycardia, possible shock |
| Temperature > 39°C | +15 | High-grade fever, systemic infection |
| Temperature < 35°C | +25 | Hypothermia risk |
| No movement for ≥ 600 seconds | +25 | Victim incapacitated or unconscious |
| No movement for ≥ 300 seconds | +10 | Early inactivity warning |
| Device offline ≥ 5 minutes | +30 | Connectivity loss, victim location unknown |
| RSSI < –100 dBm | +10 | Poor signal, data reliability reduced |
| Battery < 10% | +5 | Device may go offline soon |

Score is clamped to max 100. Priority classification:
- **P1** (Critical): score ≥ 60
- **P2** (Urgent): score 30–59
- **P3** (Stable): score < 30

### Implementation specification

```python
def compute_severity_score(
    heart_rate: int,
    temperature: float,
    sos_signal: bool,
    movement: bool,
    seconds_since_movement: int,
    rssi: int,
    battery: int,
    seconds_since_last_seen: int
) -> int:
    """
    Computes a severity score from 0–100 for a victim based on their
    current telemetry readings. Higher score = more critical.
    
    Each condition contributes a fixed point value. Points accumulate
    and are clamped to 100. This additive approach makes the contribution
    of each factor transparent and debuggable.
    """
    score = 0
    
    if sos_signal:
        score += 50
    if heart_rate < 40:
        score += 40
    elif heart_rate > 150:
        score += 20
    if temperature > 39.0:
        score += 15
    if temperature < 35.0:
        score += 25
    if seconds_since_movement >= 600:
        score += 25
    elif seconds_since_movement >= 300:
        score += 10
    if seconds_since_last_seen >= 300:
        score += 30
    if rssi < -100:
        score += 10
    if battery < 10:
        score += 5
    
    return min(score, 100)


def classify_priority(severity_score: int) -> str:
    """
    Maps a numeric severity score to a priority class (P1/P2/P3).
    Thresholds are based on standard emergency triage guidelines
    adapted for IoT-based monitoring contexts.
    """
    if severity_score >= 60:
        return "P1"
    elif severity_score >= 30:
        return "P2"
    else:
        return "P3"
```

### Thesis value
You can document the scoring matrix as a table in your thesis, justify each weight with clinical or operational reasoning, and show how changing thresholds affects triage sensitivity. This is a legitimate methodology contribution.

---

## Module 2 — Isolation Forest anomaly detector

**File**: `backend/ai/anomaly_detector.py`

**Algorithm**: Isolation Forest (scikit-learn)

**What it does**: Learns the normal pattern of vital signs during the first phase of simulation, then flags individual readings that deviate significantly from learned normality — even if they don't trigger any rule threshold.

### Why Isolation Forest?

- **Unsupervised**: does not need labelled "anomalous" data to train
- **Works on tabular data**: takes a feature vector of vitals, not raw time series
- **Fast inference**: sub-millisecond per prediction
- **Interpretable output**: returns a continuous anomaly score, not just binary
- **Works with small datasets**: can train on as few as 200 samples

### Feature vector

The model uses these 5 features per reading:
```python
features = [
    heart_rate,           # bpm
    temperature,          # °C
    float(movement),      # 0.0 or 1.0
    rssi,                 # dBm (signal quality proxy)
    battery               # % (device health proxy)
]
```

**What is excluded and why**: GPS coordinates are excluded — their drift is systematic and would confuse the anomaly detector. SOS signal is excluded — when true, it's handled by rules, not anomaly detection. Timestamp is excluded — we want location-independent anomaly detection.

### Implementation specification

```python
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class AnomalyResult:
    is_anomaly: bool
    anomaly_score: float   # negative = more anomalous; range roughly -0.5 to 0.5
    confidence: float      # mapped to 0.0–1.0 for human readability

class AnomalyDetector:
    """
    Wraps scikit-learn's IsolationForest for streaming telemetry anomaly detection.
    
    Lifecycle:
    1. Collects telemetry records until MIN_SAMPLES reached (cold start phase)
    2. Trains the model on collected "normal" data
    3. Predicts anomaly status for each new incoming record
    4. Retrains periodically on the most recent RETRAIN_WINDOW records
    
    Isolation Forest works by building random trees that isolate data points.
    Anomalous points are isolated in fewer steps (shorter paths), so they
    get lower scores. The contamination parameter tells the model what fraction
    of training data to expect as anomalous (we set low, e.g. 0.05 = 5%).
    """
    
    MIN_SAMPLES = 300          # wait for 300 readings before first training
    RETRAIN_INTERVAL = 600     # retrain every 600 new samples (≈50 minutes)
    CONTAMINATION = 0.05       # expect ~5% of training data to be anomalous
    
    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.training_buffer: list = []   # accumulates readings before first train
        self.samples_since_retrain: int = 0
        self.is_trained: bool = False
    
    def _extract_features(self, record: dict) -> list:
        return [
            record["heart_rate"],
            record["temperature"],
            float(record["movement"]),
            record["rssi"],
            record["battery"]
        ]
    
    def add_to_buffer(self, record: dict) -> None:
        """Accumulate data for training. Called for every validated packet."""
        self.training_buffer.append(self._extract_features(record))
        if len(self.training_buffer) > 2000:
            self.training_buffer = self.training_buffer[-2000:]  # keep recent only
    
    def train(self) -> None:
        """Train or retrain the model on buffered data."""
        X = np.array(self.training_buffer)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = IsolationForest(
            contamination=self.CONTAMINATION,
            random_state=42,      # reproducibility
            n_estimators=100      # number of isolation trees
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        self.samples_since_retrain = 0
    
    def predict(self, record: dict) -> AnomalyResult:
        """
        Predict whether a single record is anomalous.
        Returns AnomalyResult with is_anomaly flag and score.
        """
        self.add_to_buffer(record)
        self.samples_since_retrain += 1
        
        # Cold start: not enough data yet
        if len(self.training_buffer) < self.MIN_SAMPLES:
            return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=0.0)
        
        # First training trigger
        if not self.is_trained:
            self.train()
        
        # Periodic retraining
        if self.samples_since_retrain >= self.RETRAIN_INTERVAL:
            self.train()
        
        # Predict
        features = np.array([self._extract_features(record)])
        features_scaled = self.scaler.transform(features)
        
        # score_samples returns negative values; more negative = more anomalous
        raw_score = self.model.score_samples(features_scaled)[0]
        prediction = self.model.predict(features_scaled)[0]  # -1=anomaly, 1=normal
        
        is_anomaly = prediction == -1
        # Map raw score to 0–1 confidence (approximate)
        confidence = min(abs(raw_score) / 0.5, 1.0) if is_anomaly else 0.0
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=float(raw_score),
            confidence=float(confidence)
        )
```

### Thesis evaluation
Run 30 minutes of normal simulation, then inject 10 emergency scenarios. Record:
- True positives: anomalies correctly flagged
- False positives: normal readings incorrectly flagged
- Compute: Precision = TP / (TP + FP), Recall = TP / (TP + FN)
- Compare to rule-based-only approach

---

## Module 3 — Alert generator

**File**: `backend/ai/alert_generator.py`

**What it does**: Given the triage score result and anomaly result for a telemetry record, decides which alerts (if any) to generate, constructs human-readable messages, and returns a list of alert dictionaries for the alert_service to write.

**Key design decisions**:
- **Alert deduplication**: don't generate the same alert type for the same device more than once per 5 minutes (prevents alert storms)
- **Alert messages are human-readable**: operators should understand the alert without interpretation
- **Confidence is shown**: when an alert comes from the ML model, the confidence is included in the message

### Alert types and trigger conditions

| Alert type | Trigger condition | Severity | Message template |
|---|---|---|---|
| `sos_signal` | `sos_signal == True` | critical | "{device_id}: SOS signal activated. Immediate response required." |
| `cardiac_anomaly` | `heart_rate < 40 OR heart_rate > 150` | critical | "{device_id}: Abnormal heart rate detected ({hr} bpm). Possible cardiac event." |
| `fever_detected` | `temperature > 39.0` | warning | "{device_id}: Elevated temperature detected ({temp}°C). Possible fever or heat stroke." |
| `hypothermia_risk` | `temperature < 35.0` | critical | "{device_id}: Low body temperature ({temp}°C). Hypothermia risk." |
| `no_movement` | `seconds_since_movement >= 600` | warning | "{device_id}: No movement detected for {minutes} minutes. Victim may be unconscious." |
| `connectivity_loss` | `seconds_since_last_seen >= 300` | warning | "{device_id}: Signal lost for {minutes} minutes. Victim location unknown." |
| `ml_anomaly` | `is_anomaly == True AND confidence > 0.6` | warning | "{device_id}: Unusual vital pattern detected by AI system. Confidence: {pct}%. Manual verification recommended." |
| `p1_classification` | `priority_class == "P1"` | critical | "{device_id}: Classified as Priority 1 (Critical). Severity score: {score}/100." |
| `uav_battery_low` | UAV battery < 15% | warning | "{uav_id}: Battery at {pct}%. Return to base recommended." |

### Implementation specification

```python
from datetime import datetime, timedelta
from typing import Optional

# In-memory deduplication tracker (resets on restart — acceptable for prototype)
_last_alert_times: dict[str, datetime] = {}  # key: "device_id:alert_type"
ALERT_COOLDOWN_MINUTES = 5


def _should_alert(device_id: str, alert_type: str) -> bool:
    """
    Returns True if enough time has passed since the last alert of this
    type for this device. Prevents alert flooding during prolonged emergencies.
    """
    key = f"{device_id}:{alert_type}"
    last_time = _last_alert_times.get(key)
    if last_time is None:
        return True
    return datetime.utcnow() - last_time > timedelta(minutes=ALERT_COOLDOWN_MINUTES)


def _record_alert(device_id: str, alert_type: str) -> None:
    key = f"{device_id}:{alert_type}"
    _last_alert_times[key] = datetime.utcnow()


def decide_alerts(telemetry: dict, triage_result: dict, anomaly_result) -> list[dict]:
    """
    Determines which alerts to generate based on telemetry, triage score,
    and anomaly detection result.
    
    Returns a list of alert dicts ready for alert_service.create_alert().
    Each dict contains: device_id, alert_type, severity, message, ai_confidence.
    """
    alerts = []
    device_id = telemetry["device_id"]
    
    # Helper to add alert if cooldown allows
    def add_alert(alert_type, severity, message, confidence=1.0):
        if _should_alert(device_id, alert_type):
            alerts.append({
                "device_id": device_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "ai_confidence": confidence
            })
            _record_alert(device_id, alert_type)
    
    # Rule-based alerts
    if telemetry.get("sos_signal"):
        add_alert("sos_signal", "critical",
                  f"{device_id}: SOS signal activated. Immediate response required.")
    
    hr = telemetry.get("heart_rate", 0)
    if hr < 40:
        add_alert("cardiac_anomaly", "critical",
                  f"{device_id}: Critically low heart rate ({hr} bpm). Possible cardiac arrest.")
    elif hr > 150:
        add_alert("cardiac_anomaly", "critical",
                  f"{device_id}: Dangerously high heart rate ({hr} bpm). Possible shock.")
    
    # ... (similar for temperature, movement, connectivity)
    
    # ML-based alert (only if high confidence and cooldown passed)
    if anomaly_result.is_anomaly and anomaly_result.confidence > 0.6:
        add_alert("ml_anomaly", "warning",
                  f"{device_id}: Unusual vital pattern detected. "
                  f"AI confidence: {int(anomaly_result.confidence * 100)}%. "
                  f"Manual check recommended.",
                  confidence=anomaly_result.confidence)
    
    return alerts
```

---

## Module 4 — Pipeline composition

**File**: `backend/ai/__init__.py`

This file exports the single function that the MQTT listener calls. It chains all three modules and returns a unified result.

```python
from dataclasses import dataclass
from .triage_scorer import compute_severity_score, classify_priority
from .anomaly_detector import AnomalyDetector, AnomalyResult
from .alert_generator import decide_alerts

# Singleton detector — persists model state across requests
_detector = AnomalyDetector()

@dataclass
class AIResult:
    severity_score: int
    priority_class: str
    is_anomaly: bool
    anomaly_score: float
    ai_confidence: float
    alerts: list[dict]


def run_ai_pipeline(telemetry: dict, seconds_since_movement: int, seconds_since_last_seen: int) -> AIResult:
    """
    Main entry point for the AI layer. Called once per validated telemetry packet.
    
    Chains: triage scorer → anomaly detector → alert generator
    Returns a unified AIResult with all scoring and alert decisions.
    
    This function is a pure orchestrator — it calls the three modules
    and assembles the result. No business logic lives here.
    """
    # Step 1: Rule-based triage
    severity_score = compute_severity_score(
        heart_rate=telemetry["heart_rate"],
        temperature=telemetry["temperature"],
        sos_signal=telemetry["sos_signal"],
        movement=telemetry["movement"],
        seconds_since_movement=seconds_since_movement,
        rssi=telemetry["rssi"],
        battery=telemetry["battery"],
        seconds_since_last_seen=seconds_since_last_seen
    )
    priority_class = classify_priority(severity_score)
    triage_result = {"severity_score": severity_score, "priority_class": priority_class}
    
    # Step 2: ML anomaly detection
    anomaly_result: AnomalyResult = _detector.predict(telemetry)
    
    # Step 3: Alert generation
    alerts = decide_alerts(telemetry, triage_result, anomaly_result)
    
    return AIResult(
        severity_score=severity_score,
        priority_class=priority_class,
        is_anomaly=anomaly_result.is_anomaly,
        anomaly_score=anomaly_result.anomaly_score,
        ai_confidence=anomaly_result.confidence,
        alerts=alerts
    )
```

---

## Evaluation plan (for thesis chapter)

### Experiment 1 — Triage scorer accuracy
**Setup**: Run simulator for 30 minutes. Inject 10 scenario events (known P1 triggers) at known timestamps.

**Measure**:
```
True Positive:  AI classified P1 within 2 readings of known event start
False Positive: AI classified P1 for a device with no injected event
False Negative: Known event occurred but AI never reached P1 within 5 minutes
```

**Expected result**: Rule-based should achieve ~90% recall for threshold-triggered events. Anomaly detector adds marginal recall for gradual deterioration scenarios that don't breach thresholds.

### Experiment 2 — Anomaly detection comparison
**Comparison**: Rule-only vs Rule+IsolationForest

**Metric**: F1-score = 2 * (Precision * Recall) / (Precision + Recall)

**Hypothesis**: Hybrid approach improves recall (fewer missed anomalies) at acceptable precision cost.

### Experiment 3 — Pipeline latency
**Measure**: `time_at_mqtt_publish` vs `time_at_websocket_broadcast`

**Method**: Add timestamp logging at both points. Calculate mean latency over 500 packets.

**Expected**: < 200ms end-to-end for a local Docker deployment.

### Thesis tables to generate
| Metric | Rule-only | Hybrid (Rule+IF) |
|---|---|---|
| Precision | ? | ? |
| Recall | ? | ? |
| F1-score | ? | ? |
| Avg latency (ms) | ? | ? |
| False alarm rate (/hr) | ? | ? |
