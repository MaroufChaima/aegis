# MVP_FEATURES.md — Feature Classification (v2 — Local Dev)

> **How to use**: Before implementing any feature, check this document. MUST IMPLEMENT = required for thesis demo. PHASE 5+ = deferred complexity, implement only after Phases 1–4 are complete. CONCEPTUAL ONLY = describe in thesis, do not build.

---

## MUST IMPLEMENT
*Required. The prototype is incomplete without these.*

### Infrastructure (Local)
- [x] Python virtual environment with `requirements.txt` for backend
- [x] `package.json` with all frontend dependencies
- [x] SQLite database auto-created on first run via `init_db.py`
- [x] `.env` file for configuration (database path, CORS origins, simulator interval)
- [x] Three-terminal startup: `uvicorn`, `npm run dev`, `python simulator.py`

### Data Simulation
- [x] Python simulator generating telemetry for **15–20 virtual wearable devices**
- [x] Simulated fields per device: `device_id`, `timestamp`, GPS, `heart_rate`, `temperature`, `sos_signal`, `movement`, `rssi`, `snr`, `battery`, `uav_relay_id`
- [x] Realistic baseline values with Gaussian noise (HR ±5 bpm, temp ±0.2°C)
- [x] GPS drift per tick (victim movement simulation)
- [x] Automatic **background emergency injection** every ~180 seconds (random device goes critical)
- [x] **Named scenario functions**: SOS wave, mass casualty, UAV failure, gradual deterioration, network partition
- [x] Simulated **UAV positions** with battery drain and position drift
- [x] **Pause/resume** via shared state file (`simulator_state.json`) checked each tick
- [x] Simulator sends via **HTTP POST to `/api/ingest`** (no MQTT needed in Phase 1–4)

### Data Pipeline (FastAPI)
- [x] `POST /api/ingest` — receives telemetry from simulator, runs full pipeline
- [x] Pydantic schema validation (rejects malformed payloads with 422 response)
- [x] Duplicate detection: same `device_id + timestamp` within 2 seconds → discard
- [x] Range validation: HR (0–220 bpm), temperature (30–43°C), coordinates within bounding box
- [x] Signal quality tagging: RSSI below –100 dBm → `poor_signal` flag
- [x] Store validated telemetry to SQLite
- [x] Update device record (`last_seen`, `status`, current vitals)

### AI Module
- [x] **Rule-based severity scorer** returning score 0–100 and class P1/P2/P3:
  - SOS signal active: +50 points
  - Heart rate < 40 bpm: +40 points
  - Heart rate > 150 bpm: +20 points
  - Temperature > 39°C: +15 points
  - Temperature < 35°C: +25 points
  - No movement for ≥600 seconds: +25 points
  - No movement for ≥300 seconds: +10 points
  - Device offline for ≥5 minutes: +30 points
  - RSSI < –100 dBm: +10 points
  - Battery < 10%: +5 points
- [x] **Isolation Forest anomaly detector** (scikit-learn):
  - Cold-start: return `is_anomaly=False` until 300 samples collected
  - Train on first 300 "normal" telemetry records
  - Retrain every 600 new samples (~50 minutes)
  - Returns: `is_anomaly` (bool), `anomaly_score` (float), `confidence` (0–1)
- [x] **Alert generator** creating alert records for:
  - P1 triage classification
  - ML anomaly detection (confidence > 0.6)
  - SOS signal activation
  - Cardiac anomaly (HR < 40 or > 150)
  - No movement for 10+ minutes
  - Connectivity loss (no packet for 5+ minutes)
  - UAV battery below 15%
- [x] Alert cooldown (5-minute deduplication per device+type) to prevent alert flooding
- [x] All AI outputs stored in SQLite and broadcast via WebSocket

### REST API (FastAPI)
- [x] `POST /api/ingest` — telemetry ingest endpoint (called by simulator)
- [x] `GET /api/victims` — all devices with current status, scores, latest vitals
- [x] `GET /api/victims/{device_id}/telemetry` — last 50 readings (query param: `?limit=50`)
- [x] `GET /api/alerts` — recent alerts, filterable by severity and acknowledged status
- [x] `PATCH /api/alerts/{alert_id}/acknowledge` — mark alert as acknowledged
- [x] `GET /api/uavs` — all UAV positions and status
- [x] `GET /api/analytics/summary` — aggregated stats: victim counts by priority, alert counts by type
- [x] `GET /api/analytics/timeseries` — alert frequency last 60 minutes, binned by 5 minutes
- [x] `POST /api/simulation/scenario` — trigger named scenario
- [x] `POST /api/simulation/pause` — write `{"running": false}` to `simulator_state.json`
- [x] `POST /api/simulation/resume` — write `{"running": true}` to `simulator_state.json`
- [x] `GET /health` — returns backend + DB status

### WebSocket (FastAPI)
- [x] Endpoint: `ws://localhost:8000/ws`
- [x] Broadcasts on every processed telemetry packet and every generated alert
- [x] Message types: `telemetry_update`, `alert`, `uav_update`, `device_status_change`
- [x] Handles client disconnect gracefully (no server crash)
- [x] React reconnect logic: 3-second delay, up to 5 attempts

### React Dashboard — Overview Page (`/`)
- [x] Navigation bar with page links and live/offline WebSocket status pill
- [x] Four metric cards: Active Victims, UAVs Online, Open Alerts, Network Coverage %
- [x] **Leaflet.js zone map**:
  - Victim markers colored by priority: red=P1, orange=P2, green=P3, grey=offline
  - UAV markers with dashed coverage radius circles
  - Popup on marker click with key vitals summary
- [x] **Victim priority table**:
  - Columns: Priority, Device ID, Heart Rate, Temperature, SOS, Movement, Last Seen, Score
  - Auto-sorted descending by `severity_score`, re-sorts on every WebSocket update
  - P1 rows highlighted red, P2 rows highlighted amber
  - Click row → opens Victim Detail panel
- [x] **Alert feed**: last 15 alerts with severity icon, message, timestamp, acknowledge button

### React Dashboard — Victim Detail Panel/Modal
- [x] Heart rate line chart (last 30 readings) — Recharts LineChart
- [x] Temperature line chart (last 30 readings)
- [x] Current vitals summary cards (HR, temp, battery, RSSI, SOS status)
- [x] Alert history for this specific device
- [x] Signal quality indicator (RSSI with color coding)
- [x] Anomaly flag badge when `is_anomaly=true`

### React Dashboard — UAV Fleet Page (`/uavs`)
- [x] Responsive grid of UAV status cards (one per UAV)
- [x] Each card: UAV ID, status badge, battery bar, altitude, RSSI, connected device count
- [x] Battery bar color: green >40%, orange 15–40%, red <15%
- [x] Real-time battery drain visible across WebSocket updates

### React Dashboard — Analytics Page (`/analytics`)
- [x] Alert frequency bar chart (alerts per 5-minute bin, last 60 minutes) — Recharts BarChart
- [x] Priority distribution pie/donut chart (P1/P2/P3 counts) — Recharts PieChart
- [x] Summary stats cards: total alerts, active devices, P1 count
- [x] Average heart rate trend line chart

### React Dashboard — Simulation Control Page (`/simulation`)
- [x] Simulator status indicator (running / paused)
- [x] Pause / Resume buttons (calls `/api/simulation/pause` and `/api/simulation/resume`)
- [x] Scenario trigger buttons (each calls `POST /api/simulation/scenario`):
  - "SOS Wave" — 3 random devices send SOS simultaneously
  - "Mass Casualty Event" — 5 devices drop to critical vitals
  - "UAV Failure" — one UAV goes offline
  - "Gradual Deterioration" — one device's HR trends slowly toward dangerous range
  - "Network Partition" — one zone loses connectivity for 2 minutes
- [x] Live packet counter (packets received in last 60 seconds)

---

## PHASE 5 UPGRADES (implement only after Phases 1–4 are complete and working)

### MQTT transport
- [ ] Install Mosquitto locally (`brew install mosquitto` / `winget install mosquitto`)
- [ ] Replace simulator HTTP POST with `paho-mqtt` publish to `lorawan/{device_id}/uplink`
- [ ] Add `mqtt_client.py` to FastAPI as a background startup task (subscribes to `lorawan/+/uplink`)
- [ ] Keep `/api/ingest` as fallback — MQTT handler calls the same preprocessing pipeline

*Note: This is a nice-to-have for architectural completeness. It does not change the dashboard, AI, or database. Estimate: half a day.*

### PostgreSQL upgrade
- [ ] Install PostgreSQL locally
- [ ] Change `DATABASE_URL` in `.env` to `postgresql://aegis:password@localhost:5432/aegisdb`
- [ ] Run `alembic upgrade head` (or `init_db.py` with PostgreSQL engine)
- [ ] Test concurrent load with 20 devices posting simultaneously

### Docker Compose (thesis packaging)
- [ ] Write `docker-compose.yml` for reproducible demo environment
- [ ] Useful for: "run the demo on a different laptop" or thesis committee presentation
- [ ] Estimate: one day, after everything else works

---

## OPTIONAL ENHANCEMENTS (only if time remains)

- [ ] Dark/light mode toggle (Tailwind `dark:` classes)
- [ ] Alert sound notification (Web Audio API on new P1 alert)
- [ ] Device search/filter in victim table
- [ ] Leaflet.MarkerCluster for dense victim areas
- [ ] CSV export of telemetry for a selected device
- [ ] Animated UAV path (Leaflet Polyline showing movement trail)
- [ ] Responsive mobile layout (Tailwind breakpoints)
- [ ] WebSocket reconnection with exponential backoff

---

## CONCEPTUAL ONLY
*Do not implement. Describe in thesis design chapters.*

- **ChirpStack LoRaWAN server** — "ChirpStack decodes LoRaWAN MAC frames from physical gateways and forwards application-layer JSON to the MQTT broker on the same topic structure used by the prototype."
- **Apache Kafka** — "In production, the MQTT ingest stream would fan out to Kafka, allowing preprocessing, AI inference, archival, and logging consumers to operate independently and scale horizontally."
- **InfluxDB** — "The telemetry table would be replaced by InfluxDB for native time-series downsampling, retention policies, and sub-millisecond range queries."
- **Redis** — "Redis would cache current device state to eliminate repeated SQLite queries on the high-frequency WebSocket broadcast path."
- **Kubernetes** — "Horizontal scaling of FastAPI instances would be managed by Kubernetes in a multi-operator deployment."
- **LSTM vital trend predictor** — "An LSTM network trained on longitudinal vital data would predict deterioration 10–15 minutes before threshold breach. Requires real deployment data for meaningful training."
- **Reinforcement learning UAV router** — "An RL agent optimizing UAV positioning based on victim density and battery state is identified as future work in Chapter 7."
- **Federated learning** — "Privacy-preserving model training across multiple deployment sites, identified as a future extension."
- **Real LoRaWAN PHY simulation** — "ns-3 with the LoRaWAN module would simulate spreading factor selection, duty cycle limits, and co-channel interference."
- **End-to-end encryption** — "LoRaWAN AES-128 session encryption plus MQTT TLS client certificates would be mandatory in a production deployment."