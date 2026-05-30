# IMPLEMENTATION_ROADMAP.md — Phase-by-Phase Build Plan (v2 — Local Dev)

> **Rule**: Work through phases in order. Do not begin Phase N+1 until the checkpoint for Phase N passes. Each phase ends with a specific, verifiable test.

---

## Phase 0 — Local environment setup
**Estimated time**: 2–3 hours
**Goal**: All three services (backend, frontend, simulator skeleton) start without errors on a clean machine.

### What to create
1. `backend/requirements.txt` — all Python dependencies
2. `backend/.env` — environment variables (DATABASE_URL, CORS origins)
3. `backend/.env.example` — safe template to commit to git
4. `backend/main.py` — minimal FastAPI app with `GET /health`
5. `backend/database.py` — SQLAlchemy engine + session factory (SQLite)
6. `backend/init_db.py` — standalone script: creates all tables, seeds UAV records
7. `frontend/` — Vite + React scaffold with Tailwind configured
8. `simulator/requirements.txt` — `requests`, `numpy`, `python-dotenv`
9. `simulator/simulator.py` — skeleton that prints "tick" every 5 seconds
10. `.gitignore` — ignores `venv/`, `node_modules/`, `aegis.db`, `.env`

### No Docker, no MQTT, no Postgres
The entire stack runs in three terminals. No additional tools required beyond Python 3.11+ and Node.js 20+.

### Checkpoint ✓
```bash
# Terminal 1
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py             # should print: "Database initialized. Tables created."
uvicorn main:app --reload

# Verify:
# Browser → http://localhost:8000/health → {"status": "ok", "database": "connected"}
# Browser → http://localhost:8000/docs   → Swagger UI loads

# Terminal 2
cd frontend
npm install
npm run dev
# Browser → http://localhost:5173 → Vite default/placeholder page

# Terminal 3
cd simulator
python simulator.py
# Terminal prints: "Tick 1", "Tick 2", ... every 5 seconds
```

### Cursor session prompt
```
Refer to MASTER_CURSOR_PROMPT.md and PROJECT_CONTEXT.md.

I am starting Phase 0. Please generate:
1. backend/requirements.txt — fastapi, uvicorn, sqlalchemy, scikit-learn, numpy, pandas, python-dotenv, pydantic
2. backend/main.py — minimal FastAPI app with GET /health returning {"status": "ok", "database": "connected"}
3. backend/database.py — SQLAlchemy setup using SQLite (DATABASE_URL from .env, defaulting to sqlite:///./aegis.db)
4. backend/.env.example — all required environment variables with placeholder values
5. backend/init_db.py — standalone script that creates all tables using SQLAlchemy Base.metadata.create_all()
6. simulator/simulator.py — skeleton that just prints "Tick N" every 5 seconds in an infinite loop
7. Show me the Vite + Tailwind setup commands for the frontend (npm create vite, install tailwind, configure postcss)

Explain each file's purpose before generating it. Tell me exactly what to run and what success looks like.
```

---

## Phase 1 — Database models and schemas
**Estimated time**: 3–4 hours
**Goal**: All four SQLite tables created via SQLAlchemy models. Pydantic schemas defined. Verified by inserting a test record.

### What to create
1. `backend/models/__init__.py`
2. `backend/models/device.py` — SQLAlchemy Device model
3. `backend/models/telemetry.py` — SQLAlchemy Telemetry model
4. `backend/models/alert.py` — SQLAlchemy Alert model
5. `backend/models/uav.py` — SQLAlchemy UAVPosition model
6. `backend/schemas/__init__.py`
7. `backend/schemas/telemetry.py` — `TelemetryIn` (ingest payload), `TelemetryOut` (API response)
8. `backend/schemas/device.py` — `DeviceOut`
9. `backend/schemas/alert.py` — `AlertOut`
10. `backend/schemas/uav.py` — `UAVOut`
11. `backend/schemas/analytics.py` — `SummaryOut`, `TimeseriesOut`
12. Update `backend/init_db.py` to import all models so tables are created

### Checkpoint ✓
```bash
python init_db.py
# Should print: "Tables created: devices, telemetry, alerts, uav_positions"

# Quick verification — inspect the SQLite file:
python -c "
import sqlite3
conn = sqlite3.connect('aegis.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t[0] for t in tables])
"
# Expected: ['devices', 'telemetry', 'alerts', 'uav_positions']
```

### Cursor session prompt
```
Refer to MASTER_CURSOR_PROMPT.md and PROJECT_CONTEXT.md (database schema section).

I am in Phase 1. Please generate SQLAlchemy models for all four tables defined in PROJECT_CONTEXT.md:
- devices
- telemetry
- alerts
- uav_positions

Use SQLite-compatible types: TEXT instead of VARCHAR/TIMESTAMPTZ, INTEGER instead of BOOLEAN, REAL instead of FLOAT/DOUBLE.

Then generate the corresponding Pydantic v2 schemas for API input/output validation.

Follow FOLDER_STRUCTURE.md exactly. Explain each model's fields before generating code. After all models exist, update init_db.py to import them all so create_all() picks them up.
```

---

## Phase 2 — Python simulator
**Estimated time**: 4–6 hours
**Goal**: Simulator generates realistic telemetry for 15–20 devices and posts to FastAPI. Data visible in SQLite.

### What to create
1. `simulator/config.py` — DEVICE_IDS list, UAV_IDS, ZONE_CENTER, ZONE_RADIUS, EMIT_INTERVAL, BACKEND_URL
2. `simulator/device_model.py` — `DeviceState` class: baseline vitals, `evolve()` method adding Gaussian noise each tick
3. `simulator/uav_model.py` — `UAVState` class: position drift, battery drain
4. `simulator/scenarios.py` — scenario functions: `trigger_sos()`, `trigger_mass_casualty()`, `trigger_uav_failure()`, `trigger_deterioration()`, `trigger_network_partition()`
5. `simulator/simulator.py` — main loop: tick all devices, POST to `/api/ingest`, check `simulator_state.json` for pause

### Key behaviors
- Each device has a unique baseline HR (65–95 bpm), temperature (36.2–37.2°C), and home GPS coordinate
- Each tick adds Gaussian noise: `numpy.random.normal(0, 5)` for HR, `normal(0, 0.15)` for temperature
- One device randomly enters an emergency every ~180 seconds (background injection)
- Simulator checks `simulator_state.json` at each tick — if `{"running": false}`, sleeps and retries
- Simulator posts to `http://localhost:8000/api/ingest` using the `requests` library

### Why HTTP POST (not MQTT)?
The simulator posts JSON directly to FastAPI's REST endpoint. This means:
- Every packet is immediately visible in uvicorn's terminal log
- You can test a single packet with `curl -X POST http://localhost:8000/api/ingest -d '{...}'`
- No broker, no subscriber, no separate process, no configuration
MQTT is architecturally equivalent at this scale — both deliver JSON payloads to the backend. The difference is the transport layer, which is explicitly a prototype simplification.

### Checkpoint ✓
```bash
# With backend running in Terminal 1, start simulator in Terminal 3:
python simulator.py

# In backend terminal, you should see:
# INFO: POST /api/ingest 200 OK  (repeated every 5 seconds for each device)

# Check database:
python -c "
import sqlite3
conn = sqlite3.connect('backend/aegis.db')
rows = conn.execute('SELECT device_id, heart_rate, temperature FROM telemetry ORDER BY rowid DESC LIMIT 5').fetchall()
print(rows)
"
# Expected: 5 rows with different device IDs and realistic vital values
```

### Cursor session prompt
```
Refer to MASTER_CURSOR_PROMPT.md and PROJECT_CONTEXT.md (Layer 1 — Data Collection).

I am in Phase 2. Please generate:
1. simulator/config.py — 15 device IDs (WB-001 to WB-015), 3 UAV IDs (UAV-01 to UAV-03), Sétif Algeria zone center (36.19°N, 5.41°E), emit interval 5 seconds, backend URL http://localhost:8000
2. simulator/device_model.py — DeviceState class. Each device has: baseline_hr (random 65–95), baseline_temp (random 36.2–37.2), home_lat, home_lon, current_lat, current_lon, seconds_since_movement counter, is_in_emergency flag. The evolve() method adds realistic Gaussian noise each tick.
3. simulator/scenarios.py — functions for each of the 5 named scenarios. Each function modifies specific DeviceState objects to simulate the emergency.
4. simulator/simulator.py — main loop: create all DeviceState objects, run infinite loop, call evolve() on each, POST JSON to /api/ingest, check simulator_state.json for pause signal, auto-inject random emergencies every ~180 seconds.

Use the requests library for HTTP. Explain the noise model (Gaussian distribution) in comments.
```

---

## Phase 3 — Ingest pipeline and services
**Estimated time**: 4–5 hours
**Goal**: FastAPI validates, preprocesses, and persists every simulator packet. AI not yet integrated — just clean data storage.

### What to create
1. `backend/services/__init__.py`
2. `backend/services/preprocessing.py` — `validate_ranges()`, `deduplicate()`, `tag_signal_quality()`
3. `backend/services/device_service.py` — `upsert_device()`, `update_device_status()`
4. `backend/services/telemetry_service.py` — `insert_telemetry()`, `get_device_history()`
5. `backend/services/alert_service.py` — `create_alert()`, `get_recent_alerts()`
6. `backend/routers/__init__.py`
7. `backend/routers/ingest.py` — `POST /api/ingest` route that calls preprocessing + services
8. Update `backend/main.py` — include the ingest router

### Key behaviors
- `POST /api/ingest` receives `TelemetryIn` payload, runs preprocessing, writes to DB, returns 200
- Duplicate detection: query last telemetry for this `device_id`, reject if same timestamp ±2 seconds
- Range validation logs a warning but does **not** crash the server — return 422 with explanation
- `upsert_device()`: if device_id doesn't exist, INSERT new device record; else UPDATE `last_seen`, `status`

### Checkpoint ✓
```bash
# Test a single manual ingest:
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "WB-001",
    "timestamp": "2025-01-15T14:23:01Z",
    "latitude": 36.19, "longitude": 5.41,
    "heart_rate": 87, "temperature": 37.2,
    "sos_signal": false, "movement": true,
    "rssi": -84, "snr": 7.2,
    "battery": 78, "uav_relay_id": "UAV-01"
  }'
# Expected: {"status": "ok", "device_id": "WB-001", "severity_score": 0}

# Then with simulator running, check DB has data:
python -c "import sqlite3; c=sqlite3.connect('backend/aegis.db'); print(c.execute('SELECT COUNT(*) FROM telemetry').fetchone())"
# Expected after 1 minute: count > 100
```

### Cursor session prompt
```
Refer to MASTER_CURSOR_PROMPT.md, PROJECT_CONTEXT.md (Layer 2 — Preprocessing), and API_FLOW.md.

I am in Phase 3. The simulator is posting to /api/ingest. Now I need FastAPI to:
1. Validate the payload using the TelemetryIn Pydantic schema
2. Run preprocessing: deduplicate() checks DB for same device_id + timestamp within 2s; validate_ranges() checks HR 0–220 and temp 30–43; tag_signal_quality() sets poor_signal flag for RSSI < -100
3. Upsert the device record (insert if new, update last_seen and status if existing)
4. Insert the telemetry record

Generate services/preprocessing.py, services/device_service.py, services/telemetry_service.py, and routers/ingest.py.

The AI pipeline is NOT integrated yet — just placeholder values (severity_score=0, is_anomaly=False) for now. Explain the upsert pattern before generating device_service.py.
```

---

## Phase 4 — AI pipeline integration
**Estimated time**: 4–6 hours
**Goal**: Every ingested packet passes through the AI pipeline. Severity scores, anomaly flags, and alerts appear in the database.

### What to create
1. `backend/ai/__init__.py` — exports `run_ai_pipeline()` and `AIResult`
2. `backend/ai/triage_scorer.py` — `compute_severity_score()`, `classify_priority()`
3. `backend/ai/anomaly_detector.py` — `AnomalyDetector` class wrapping IsolationForest
4. `backend/ai/alert_generator.py` — `decide_alerts()` with 5-minute cooldown deduplication
5. Update `backend/routers/ingest.py` — call `run_ai_pipeline()` after preprocessing, pass result to services

### Key behaviors (from SIMPLIFIED_AI_MODULES.md)
- Triage scorer: additive weighted scoring, clamped to 100
- Anomaly detector: cold-start returns `is_anomaly=False` until 300 samples collected
- Alert cooldown: `_last_alert_times` dict prevents repeat alerts within 5 minutes per device+type
- P1 devices trigger an additional `p1_classification` alert on first classification

### Checkpoint ✓
```bash
# Run simulator for 2 minutes, then check:
python -c "
import sqlite3
conn = sqlite3.connect('backend/aegis.db')
print('=== Devices with scores ===')
print(conn.execute('SELECT device_id, severity_score, priority_class FROM devices ORDER BY severity_score DESC').fetchall())
print('=== Recent alerts ===')
print(conn.execute('SELECT device_id, alert_type, severity, message FROM alerts ORDER BY rowid DESC LIMIT 5').fetchall())
"
# Expected: at least one device with non-zero score; alert records present after emergency injection
```

### Cursor session prompt
```
Refer to MASTER_CURSOR_PROMPT.md and SIMPLIFIED_AI_MODULES.md.

I am in Phase 4. Please generate all four AI module files:
1. ai/triage_scorer.py — exactly the scoring weights defined in SIMPLIFIED_AI_MODULES.md
2. ai/anomaly_detector.py — IsolationForest wrapper with cold-start handling, StandardScaler, and the 5-feature vector (heart_rate, temperature, movement, rssi, battery). Use MIN_SAMPLES=300, CONTAMINATION=0.05.
3. ai/alert_generator.py — decide_alerts() with in-memory cooldown deduplication dict
4. ai/__init__.py — run_ai_pipeline() singleton that chains all three

Then update routers/ingest.py to:
- Call run_ai_pipeline() after preprocessing
- Pass severity_score and priority_class to device_service.update_device()
- Pass is_anomaly and severity_score to telemetry_service.insert_telemetry()
- Call alert_service.create_alert() for each alert in the result

Explain the Isolation Forest algorithm in comments: what "contamination" means, why it works unsupervised, and what the anomaly score represents.
```

---

## Phase 5 — REST API and WebSocket
**Estimated time**: 4–5 hours
**Goal**: All API endpoints working. WebSocket broadcasting live updates to connected clients.

### What to create
1. `backend/websocket_manager.py` — `ConnectionManager` class: track connections, broadcast JSON
2. `backend/routers/victims.py` — `GET /api/victims`, `GET /api/victims/{id}/telemetry`
3. `backend/routers/alerts.py` — `GET /api/alerts`, `PATCH /api/alerts/{id}/acknowledge`
4. `backend/routers/uavs.py` — `GET /api/uavs`
5. `backend/routers/analytics.py` — `GET /api/analytics/summary`, `GET /api/analytics/timeseries`
6. `backend/routers/simulation.py` — `POST /api/simulation/scenario`, `/pause`, `/resume`
7. Update `backend/main.py` — include all routers, add `ws://localhost:8000/ws` endpoint
8. Update `backend/routers/ingest.py` — broadcast via WebSocket after AI pipeline completes

### WebSocket broadcast points
- After every successful `POST /api/ingest`: broadcast `telemetry_update`
- For every alert generated: broadcast `alert`
- Simulator UAV tick: broadcast `uav_update` (UAVs updated every 10 seconds)

### Checkpoint ✓
```bash
# All endpoints visible:
# Browser → http://localhost:8000/docs

# Test WebSocket in browser console (F12):
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
# Should see JSON messages arriving every 5 seconds

# Test REST endpoint:
curl http://localhost:8000/api/victims
# Expected: JSON array of devices with severity_score and priority_class
```

### Cursor session prompt
```
Refer to MASTER_CURSOR_PROMPT.md, API_FLOW.md, and FOLDER_STRUCTURE.md.

I am in Phase 5. Please generate:
1. websocket_manager.py — ConnectionManager with connect(), disconnect(), broadcast(json_message) methods
2. All five router files with the endpoints defined in API_FLOW.md
3. The WebSocket endpoint at /ws in main.py
4. Update routers/ingest.py to call websocket_manager.broadcast() after AI pipeline

For analytics/timeseries, write a SQLAlchemy raw SQL query that bins alerts into 5-minute intervals using SQLite's strftime() function (not PostgreSQL's date_trunc). Explain the time-binning approach in comments.

Show me the full updated main.py after all routers and the WebSocket endpoint are added.
```

---

## Phase 6 — React dashboard
**Estimated time**: 5–7 days (largest phase, split into sub-phases)
**Goal**: Full interactive dashboard connected to the backend. All five pages working.

### 6a — Foundation and WebSocket (half day)
- Install dependencies: `npm install react-router-dom react-leaflet leaflet recharts`
- Add Leaflet CSS to `index.html`
- Create `contexts/WebSocketContext.jsx` — WebSocket connection, message routing by `type`, state for victims/alerts/uavs
- Create custom hooks: `useVictims.js`, `useAlerts.js`, `useUAVs.js`
- Create app shell: `App.jsx` with React Router routes, `NavigationBar.jsx`
- Create `api/` fetch functions for all endpoints

**Checkpoint**: Browser console shows WebSocket messages arriving. `/docs` visible in Swagger.

### 6b — Overview page: metrics + table + alert feed (1 day)
- `components/metrics/MetricStrip.jsx` + `MetricCard.jsx`
- `components/victims/VictimTable.jsx` — sorted by severity_score, P1 rows highlighted red
- `components/victims/VictimRow.jsx`
- `components/alerts/AlertFeed.jsx` + `AlertRow.jsx`
- Wire all components to WebSocketContext

**Checkpoint**: Overview page shows live-updating table and alert feed.

### 6c — Zone map (1 day)
- `components/map/ZoneMap.jsx` — react-leaflet MapContainer
- `components/map/VictimMarker.jsx` — colored by priority, popup with vitals
- `components/map/UAVMarker.jsx` — distinct icon, dashed coverage Circle
- Import `leaflet/dist/leaflet.css` (common gotcha: maps appear grey without this)

**Checkpoint**: Map shows victim markers and UAV circles. Markers update color when priority changes.

### 6d — Victim detail + UAV fleet (1 day)
- `components/victims/VictimDetail.jsx` — modal/panel, fetches `/api/victims/{id}/telemetry`
- `components/charts/HeartRateChart.jsx` — Recharts LineChart
- `components/charts/TemperatureChart.jsx`
- `pages/UAVFleetPage.jsx` with `UAVGrid.jsx` + `UAVCard.jsx`

**Checkpoint**: Clicking a victim row opens detail panel with charts. UAV Fleet page shows battery bars.

### 6e — Analytics + Simulation pages (1 day)
- `pages/AnalyticsPage.jsx`
- `components/charts/AlertFrequency.jsx` — Recharts BarChart
- `components/charts/PriorityPie.jsx` — Recharts PieChart
- `pages/SimulationPage.jsx` with `ScenarioPanel.jsx` + `ScenarioButton.jsx`

**Checkpoint**: Trigger "Mass Casualty Event" → alert appears in feed within 5 seconds → P1 markers appear on map.

### Cursor session prompt for 6a
```
Refer to MASTER_CURSOR_PROMPT.md and FOLDER_STRUCTURE.md (frontend section).

I am starting Phase 6a. Please:
1. Show me the exact npm install command for all frontend dependencies (react-router-dom, react-leaflet, leaflet, recharts)
2. Generate contexts/WebSocketContext.jsx — connects to ws://localhost:8000/ws, routes messages by type field (telemetry_update updates victims array, alert prepends to alerts array, uav_update updates UAVs array), exposes {victims, alerts, uavs, connectionStatus} to all children, attempts reconnect on disconnect with 3-second delay
3. Generate api/victims.js, api/alerts.js, api/uavs.js, api/analytics.js, api/simulation.js — simple fetch() wrappers for each REST endpoint
4. Generate App.jsx with React Router v6 routes for 5 pages, and NavigationBar.jsx with a live status pill (green if WebSocket connected, red if disconnected)

Explain the React Context + Provider pattern before generating the WebSocketContext, since I need to understand it for the thesis.
```

---

## Phase 7 — Evaluation and thesis polish
**Estimated time**: 2–3 days
**Goal**: Structured experiments completed and recorded. UI polished. Thesis materials prepared.

### Experiments

**Experiment 1 — Triage accuracy**
- Run simulator 30 minutes
- Inject 10 known P1 events at known timestamps using `/api/simulation/scenario`
- Query DB to check: how many devices reached P1 within 2 telemetry packets of event start?
- Record: True Positive, False Positive, False Negative rates
- Generate confusion matrix table for thesis

**Experiment 2 — Rule-based vs hybrid comparison**
- Add a `RULE_ONLY_MODE` flag to `ai/__init__.py` that disables the Isolation Forest
- Run 30 minutes in rule-only mode, export alert precision/recall
- Re-run with Isolation Forest enabled, export alert precision/recall
- Compare: does anomaly detection improve recall without unacceptable false positive increase?

**Experiment 3 — Pipeline latency**
- Add `ingest_timestamp` logging at the start and end of `POST /api/ingest` processing
- Run 500 packets, calculate mean end-to-end latency
- Target: < 50ms per packet on local machine

**Experiment 4 — WebSocket delivery latency**
- Add `broadcast_timestamp` to WebSocket messages
- In React, record `Date.now()` when message arrives
- Calculate mean time from simulator POST to React receipt across 100 messages

### UI polish
- Loading skeletons while API data fetches on initial page load
- Empty state components for pages with no data yet
- Error toast if WebSocket disconnects
- Consistent color palette across all pages (use `utils/priorityColors.js` as single source of truth)

### Thesis materials
- Screenshots of all five pages in active simulation
- 2–3 minute screen recording: start simulator → emergency injection → alert → map update → victim detail charts
- Export experiment result tables to CSV

### Checkpoint ✓
- Demo video shows full end-to-end flow
- Experiment tables have data for thesis Chapter 5 (Evaluation)
- All five pages render without console errors
- `uvicorn main:app` + `npm run dev` + `python simulator.py` starts cleanly on first attempt

---

## Optional Phase 8 — MQTT and Docker (if time allows)
**Estimated time**: 1–2 days
**Goal**: Replace HTTP simulator transport with MQTT. Add Docker Compose for demo packaging.

### MQTT upgrade
1. Install Mosquitto locally
2. Add `paho-mqtt` to `backend/requirements.txt`
3. Create `backend/mqtt_client.py` — connects to Mosquitto on startup, subscribes to `lorawan/+/uplink`, calls same preprocessing pipeline as `/api/ingest`
4. Update simulator to publish via paho-mqtt instead of HTTP POST
5. Keep `/api/ingest` endpoint active — useful for manual testing and fallback

### Docker Compose (packaging)
1. Write `docker-compose.yml` with: postgres, mosquitto, backend, simulator, frontend
2. Write `backend/Dockerfile` and `frontend/Dockerfile`
3. Test: `docker compose up` starts all services cleanly
4. This is the "reproducible demo" artifact for thesis submission

---

## Summary timeline

| Phase | Goal | Estimated time |
|---|---|---|
| 0 | Environment setup | 2–3 hrs |
| 1 | DB models and schemas | 3–4 hrs |
| 2 | Python simulator | 4–6 hrs |
| 3 | Ingest pipeline | 4–5 hrs |
| 4 | AI pipeline | 4–6 hrs |
| 5 | REST API + WebSocket | 4–5 hrs |
| 6 | React dashboard | 5–7 days |
| 7 | Evaluation + polish | 2–3 days |
| 8 (optional) | MQTT + Docker | 1–2 days |

**Total Phase 0–7**: approximately 3–4 weeks of implementation work at moderate pace.