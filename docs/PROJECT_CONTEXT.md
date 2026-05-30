# PROJECT_CONTEXT.md — AEGIS Platform Architecture Reference (v2 — Local Dev)

> **Purpose**: Single source of truth for the AEGIS prototype architecture. Reference at the start of every Cursor session. Answers: "What are we building and how does it fit together?"

---

## Project objective

Design and implement a prototype **Intelligent Emergency Management Platform** that demonstrates how a UAV-assisted LoRaWAN network could support disaster response operations. The platform ingests simulated IoT wearable telemetry, applies AI-based triage and anomaly detection, and presents real-time situational awareness to emergency operators through a web dashboard.

This is a **thesis prototype** running entirely locally — no Docker, no cloud, no message broker in Phase 1–4. The goal is to validate the architecture, demonstrate the data pipeline, and evaluate the AI decision-support logic against simulated emergency scenarios.

---

## System layers

### Layer 1 — Data Collection (simulated)
In a real deployment: wearable IoT devices → LoRaWAN uplink → UAV aerial gateway → UAV Base Station → cloud.

In this prototype: a **Python simulator** generates realistic telemetry for 15–20 virtual devices and sends it via HTTP POST to the FastAPI backend. This replicates the JSON payload structure a real LoRaWAN network server (e.g., ChirpStack) would produce.

**Why HTTP instead of MQTT for Phase 1?** MQTT introduces a separate broker process, connection configuration, and a new debugging surface. HTTP POST to FastAPI is immediately inspectable in the uvicorn logs, testable with curl, and produces zero additional setup steps. The architecture documents MQTT as the production transport — the simulator is explicitly a simulation layer. In Phase 5, if time permits, MQTT can replace the HTTP transport without changing any other layer.

**Simulated data per device (posted every 5 seconds):**
```json
{
  "device_id": "WB-007",
  "timestamp": "2025-01-15T14:23:01Z",
  "latitude": 36.7321,
  "longitude": 3.0841,
  "heart_rate": 87,
  "temperature": 37.2,
  "sos_signal": false,
  "movement": true,
  "rssi": -84,
  "snr": 7.2,
  "battery": 78,
  "uav_relay_id": "UAV-02"
}
```

### Layer 2 — Preprocessing and Ingestion
FastAPI receives telemetry via `POST /api/ingest`. On every packet:

1. **Schema validation** — Pydantic model rejects malformed payloads (wrong types, missing fields)
2. **Duplicate detection** — reject if same device_id + timestamp within 2-second window
3. **Range validation** — HR must be 0–220, temperature 30–43, coordinates within defined zone
4. **Signal quality tagging** — RSSI below –100 dBm tagged as `poor_signal`
5. **Storage** — validated telemetry written to SQLite via SQLAlchemy

### Layer 3 — Intelligent Analytics
After preprocessing, each telemetry record passes through the AI pipeline:

1. **Rule-based triage scorer** — computes `severity_score` (0–100) and priority class (P1/P2/P3)
2. **Isolation Forest anomaly detector** — flags statistically unusual vital patterns
3. **Alert generator** — writes Alert records when thresholds or anomaly conditions are met
4. Results broadcast via WebSocket to all connected React clients

### Layer 4 — Decision Support and Visualization
React dashboard with five main views:

| Page | Content |
|---|---|
| Overview | Metric cards, zone map, victim priority table, alert feed |
| UAV Fleet | Per-UAV status cards with battery, altitude, coverage |
| Victim Detail | Telemetry history charts, vitals timeline |
| Analytics | Alert frequency, priority distribution, signal quality trends |
| Simulation Control | Scenario injection, pause/resume |

---

## Technology stack

```
Frontend:   React 18 + Vite + Tailwind CSS + react-leaflet + Recharts
Backend:    FastAPI (Python 3.11) + SQLAlchemy
Database:   SQLite (file: backend/aegis.db)  ←  zero setup
AI/ML:      scikit-learn (IsolationForest)
Realtime:   FastAPI native WebSockets
Transport:  HTTP POST (Phase 1–4) / MQTT optional (Phase 5)
DevEnv:     Local — Python venv + Node.js, no Docker
```

---

## Communication flow (Phase 1–4)

```
Python Simulator (simulator/simulator.py)
    │
    │  HTTP POST every 5 seconds
    │  → POST /api/ingest  (one request per device per tick)
    ▼
FastAPI (uvicorn, port 8000)
    │
    ├── Pydantic validation
    ├── Preprocessing (deduplicate, range-check, tag)
    ├── AI pipeline (triage score, anomaly detect, alerts)
    ├── SQLite write (SQLAlchemy)
    │
    └── WebSocket broadcast → connected React clients
            │
            ▼
    React Dashboard (Vite dev server, port 5173)
        ├── Map updates victim/UAV markers
        ├── Priority table re-sorts
        ├── Alert feed prepends new alerts
        └── Charts append new data points
```

**REST API** is used for:
- Initial page load (fetch all current state)
- Historical telemetry for charts
- Simulation control (pause, resume, trigger scenarios)
- Analytics aggregations

**WebSocket** is used for:
- All real-time updates (telemetry, alerts, UAV positions)
- Push-based: server broadcasts, client never polls

---

## Database schema (SQLite via SQLAlchemy)

```sql
-- Registered wearable devices
devices (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id       TEXT UNIQUE NOT NULL,      -- e.g. "WB-007"
  name            TEXT,
  status          TEXT DEFAULT 'online',     -- online | offline | sos
  severity_score  INTEGER DEFAULT 0,         -- 0–100, updated by AI module
  priority_class  TEXT DEFAULT 'P3',         -- P1 | P2 | P3
  anomaly_flag    INTEGER DEFAULT 0,         -- SQLite boolean: 0/1
  last_seen       TEXT,                      -- ISO timestamp
  uav_relay_id    TEXT                       -- which UAV serves this device
)

-- Raw telemetry stream (append-only)
telemetry (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id       TEXT NOT NULL,
  timestamp       TEXT NOT NULL,
  latitude        REAL,
  longitude       REAL,
  heart_rate      INTEGER,
  temperature     REAL,
  sos_signal      INTEGER,                   -- 0/1
  movement        INTEGER,                   -- 0/1
  rssi            INTEGER,
  snr             REAL,
  battery         INTEGER,
  is_anomaly      INTEGER DEFAULT 0,
  severity_score  INTEGER DEFAULT 0,
  FOREIGN KEY (device_id) REFERENCES devices(device_id)
)

-- Generated alerts
alerts (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id       TEXT NOT NULL,
  timestamp       TEXT DEFAULT (datetime('now')),
  alert_type      TEXT,   -- sos_signal | cardiac_anomaly | no_movement | connectivity_loss | ml_anomaly | p1_classification | uav_battery_low
  severity        TEXT,   -- critical | warning | info
  message         TEXT,
  acknowledged    INTEGER DEFAULT 0,
  ai_confidence   REAL DEFAULT 1.0
)

-- Simulated UAV positions (upserted on each UAV tick)
uav_positions (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  uav_id            TEXT UNIQUE NOT NULL,   -- e.g. "UAV-01"
  timestamp         TEXT DEFAULT (datetime('now')),
  latitude          REAL,
  longitude         REAL,
  altitude          REAL,
  battery           INTEGER,
  status            TEXT DEFAULT 'active',  -- active | returning | offline
  coverage_radius   REAL DEFAULT 800.0,
  connected_devices INTEGER DEFAULT 0
)
```

**Note on SQLite**: `BOOLEAN` becomes `INTEGER` (0/1) and `TIMESTAMPTZ` becomes `TEXT` in SQLite. SQLAlchemy handles these transparently. When upgrading to PostgreSQL, only the `DATABASE_URL` in `.env` changes — the ORM models stay identical.

---

## Starting the full stack (3 commands)

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py        # creates aegis.db and all tables
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev              # starts on http://localhost:5173

# Terminal 3 — Simulator
cd simulator
python simulator.py      # starts posting telemetry every 5 seconds
```

All three processes print logs directly to their terminal. No Docker. No service orchestration.

---

## MVP goals

Complete when the prototype demonstrates:

1. ✅ Simulator → HTTP POST → FastAPI → SQLite pipeline
2. ✅ Preprocessing: validation, deduplication, range checks
3. ✅ AI triage scoring (rule-based severity score + Isolation Forest flag)
4. ✅ Alert generation for cardiac events, SOS, inactivity, connectivity loss
5. ✅ Real-time WebSocket push to dashboard
6. ✅ Interactive Leaflet map with color-coded victim markers and UAV coverage circles
7. ✅ Victim priority table sorted by severity score, auto-updating
8. ✅ Telemetry history charts for selected victim (Recharts)
9. ✅ Alert feed with severity color coding
10. ✅ UAV fleet status panel
11. ✅ Simulation control panel (trigger scenarios, pause/resume)
12. ✅ Analytics summary page with charts

---

## Conceptual components (thesis design only — not implemented)

These appear in thesis architecture diagrams and design chapters, but are NOT implemented in the prototype:

| Component | Why not implemented | How to describe in thesis |
|---|---|---|
| MQTT / Mosquitto | Phase 5 upgrade only | "The HTTP ingest endpoint simulates the JSON output a LoRaWAN network server would deliver via MQTT. Phase 5 introduces the MQTT transport layer to demonstrate production-parity message flow." |
| ChirpStack LoRaWAN server | Requires real LoRa hardware | "ChirpStack would replace the Python simulator in a real deployment, decoding LoRaWAN MAC frames and forwarding JSON to the MQTT broker." |
| PostgreSQL | SQLite used for development | "The SQLAlchemy ORM layer abstracts the database. Replacing SQLite with PostgreSQL requires only changing the DATABASE_URL — all queries remain identical." |
| Apache Kafka | No need at prototype scale | "In production, MQTT messages would be forwarded to Kafka for scalable, durable event streaming with multiple independent consumers." |
| Redis | No performance need | "Redis would cache current device state to reduce SQLite/Postgres query load in high-frequency broadcast paths." |
| Docker Compose | Deliberately deferred | "The production deployment would containerize all services with Docker Compose. The development environment runs each service locally for debugging transparency." |
| LSTM predictor | Insufficient training data | "LSTM-based vital trend prediction is identified as future work requiring months of real deployment data." |
| Reinforcement learning UAV router | Requires real UAV coordination | "An RL agent optimizing UAV positioning dynamically is a future extension documented in Chapter 7." |

---

## Key design decisions and rationale

**Why SQLite over PostgreSQL for development?**
SQLite requires zero installation, zero configuration, and produces a single file you can inspect, copy, and delete. A database connection failure is the most common setup blocker for new projects. Eliminating it means implementation starts immediately. SQLAlchemy abstracts the difference so upgrading to PostgreSQL is a one-line change.

**Why HTTP POST instead of MQTT for Phase 1?**
Every MQTT packet is invisible unless you run a separate subscriber tool. Every HTTP POST is visible in the uvicorn terminal log, testable with curl or the Swagger UI at `/docs`, and immediately debuggable. For a one-student prototype with a 3–4 week implementation window, this difference is significant. MQTT is introduced in Phase 5 as an optional architectural upgrade.

**Why WebSockets for real-time updates?**
An emergency management system requires sub-second alert delivery. Polling every 3 seconds would delay critical alerts and waste resources. FastAPI's native WebSocket support makes push-based updates straightforward without additional dependencies.

**Why scikit-learn Isolation Forest?**
Trains on tens of minutes of simulated data, requires no labelled training set, produces explainable anomaly scores, and runs in sub-millisecond per prediction. Deep learning alternatives would require months of real deployment data and add implementation complexity without improving prototype validity.

**Why no Docker in Phase 1–4?**
Docker adds value for reproducible multi-service deployment but costs significant setup time and debugging complexity for solo development. Typical Docker issues (port conflicts, volume mounts, container networking, WSL disk performance) are all irrelevant problems when the goal is a working prototype. Docker can be added after the prototype is validated — not before.