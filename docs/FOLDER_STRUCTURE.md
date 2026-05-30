# FOLDER_STRUCTURE.md — Project File Organization

> Every file has a designated place. When asking Cursor to generate a file, always specify the path from this document. Never put business logic in route files, never put database queries in AI files.

---

## Root structure

```
aegis/                              ← project root
│
├── docker-compose.yml              ← defines all services and their connections
├── .env                            ← shared environment variables (never commit this)
├── .env.example                    ← safe template with placeholder values (commit this)
├── .gitignore
├── README.md
│
├── docs/                           ← AI-assisted dev package (these files)
│   ├── MASTER_CURSOR_PROMPT.md
│   ├── PROJECT_CONTEXT.md
│   ├── MVP_FEATURES.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── FOLDER_STRUCTURE.md
│   ├── API_FLOW.md
│   └── SIMPLIFIED_AI_MODULES.md
│
├── backend/                        ← FastAPI Python application
├── frontend/                       ← React + Vite application
├── simulator/                      ← Python telemetry simulator
└── mosquitto/                      ← MQTT broker configuration
```

---

## Backend structure

```
backend/
│
├── Dockerfile                      ← builds the backend container image
├── requirements.txt                ← all Python dependencies
├── .env                            ← backend-specific env vars (DATABASE_URL, etc.)
├── alembic.ini                     ← Alembic migration tool config
│
├── main.py                         ← FastAPI app entry point
│                                      Responsibilities: create app, include routers,
│                                      register startup/shutdown events, mount WebSocket
│
├── database.py                     ← SQLAlchemy engine and session factory
│                                      Responsibilities: create engine from DATABASE_URL,
│                                      provide get_db() dependency for route injection
│
├── mqtt_client.py                  ← MQTT subscriber (paho-mqtt)
│                                      Responsibilities: connect to Mosquitto on startup,
│                                      subscribe to lorawan/+/uplink, call preprocessing
│                                      pipeline on each received message
│
├── websocket_manager.py            ← WebSocket connection pool
│                                      Responsibilities: track active connections,
│                                      broadcast JSON messages to all clients,
│                                      handle connect/disconnect gracefully
│
├── models/                         ← SQLAlchemy ORM models (Python ↔ database tables)
│   ├── __init__.py                 ← imports all models so Alembic finds them
│   ├── device.py                   ← Device model (devices table)
│   ├── telemetry.py                ← Telemetry model (telemetry table)
│   ├── alert.py                    ← Alert model (alerts table)
│   └── uav.py                      ← UAVPosition model (uav_positions table)
│
├── schemas/                        ← Pydantic models for API validation and serialization
│   ├── __init__.py
│   ├── telemetry.py                ← TelemetryIn (MQTT payload), TelemetryOut (API response)
│   ├── device.py                   ← DeviceOut, DeviceListOut
│   ├── alert.py                    ← AlertOut, AlertAcknowledge
│   ├── uav.py                      ← UAVOut
│   └── analytics.py                ← SummaryOut, TimeseriesOut
│
├── routers/                        ← FastAPI route handlers (thin layer, no business logic)
│   ├── __init__.py
│   ├── victims.py                  ← GET /api/victims, GET /api/victims/{id}/telemetry
│   ├── alerts.py                   ← GET /api/alerts, PATCH /api/alerts/{id}/acknowledge
│   ├── uavs.py                     ← GET /api/uavs
│   ├── analytics.py                ← GET /api/analytics/summary, /timeseries
│   └── simulation.py               ← POST /api/simulation/scenario, /pause, /resume
│
├── services/                       ← Business logic layer (called by routers and mqtt_client)
│   ├── __init__.py
│   ├── preprocessing.py            ← validate(), deduplicate(), tag_signal_quality()
│   │                                  Input: raw MQTT dict
│   │                                  Output: validated TelemetryIn or raises ValidationError
│   ├── device_service.py           ← upsert_device(), update_device_status()
│   │                                  Input: validated telemetry
│   │                                  Output: Device record
│   ├── telemetry_service.py        ← insert_telemetry(), get_device_history()
│   │                                  Input: validated telemetry + AI results
│   │                                  Output: Telemetry record
│   └── alert_service.py            ← create_alert(), get_recent_alerts()
│                                      Input: device_id + alert_type + message
│                                      Output: Alert record
│
├── ai/                             ← AI/ML modules (pure functions, no DB access)
│   ├── __init__.py                 ← exports run_ai_pipeline(telemetry) -> AIResult
│   ├── triage_scorer.py            ← compute_severity_score(), classify_priority()
│   │                                  Input: telemetry dict + device history
│   │                                  Output: (severity_score: int, priority_class: str)
│   ├── anomaly_detector.py         ← AnomalyDetector class wrapping IsolationForest
│   │                                  Methods: fit(data), predict(record), retrain()
│   └── alert_generator.py          ← decide_alerts()
│                                      Input: telemetry + AIResult
│                                      Output: list of alert dicts to create
│
└── alembic/                        ← database migration files
    ├── env.py                      ← Alembic environment (auto-configured)
    ├── script.py.mako
    └── versions/
        └── 001_initial_schema.py   ← creates all four tables
```

### Backend file responsibilities — the rule
> **Routers know about schemas and services. Services know about models and database. AI modules know about neither — they are pure functions taking dicts and returning dicts. This separation makes each layer independently testable.**

---

## Frontend structure

```
frontend/
│
├── Dockerfile                      ← builds production nginx container
├── package.json
├── vite.config.js                  ← Vite config: proxy /api → backend, /ws → backend
├── tailwind.config.js
├── postcss.config.js
├── index.html                      ← single HTML entry point
│
└── src/
    │
    ├── main.jsx                    ← React app entry: wraps App in all context providers
    ├── App.jsx                     ← React Router routes definition
    │
    ├── contexts/                   ← React Context providers (global shared state)
    │   ├── WebSocketContext.jsx    ← opens WS connection, routes messages by type,
    │   │                              exposes: victims, alerts, uavs, connectionStatus
    │   └── SimulationContext.jsx   ← tracks simulator status (running/paused)
    │
    ├── hooks/                      ← Custom React hooks (reusable logic)
    │   ├── useWebSocket.js         ← low-level WS connection management + reconnect
    │   ├── useVictims.js           ← subscribe to victim updates, expose sorted list
    │   ├── useAlerts.js            ← subscribe to alert updates, expose recent list
    │   └── useUAVs.js              ← subscribe to UAV updates
    │
    ├── pages/                      ← Top-level page components (one per route)
    │   ├── OverviewPage.jsx        ← route: /
    │   ├── UAVFleetPage.jsx        ← route: /uavs
    │   ├── AnalyticsPage.jsx       ← route: /analytics
    │   └── SimulationPage.jsx      ← route: /simulation
    │
    ├── components/                 ← Reusable UI components (no data fetching here)
    │   │
    │   ├── layout/
    │   │   ├── NavigationBar.jsx   ← top nav with page links, live status pill
    │   │   ├── PageContainer.jsx   ← consistent page padding wrapper
    │   │   └── Sidebar.jsx         ← optional left sidebar (if used)
    │   │
    │   ├── map/
    │   │   ├── ZoneMap.jsx         ← react-leaflet MapContainer, manages all layers
    │   │   ├── VictimMarker.jsx    ← single Leaflet marker with priority color + popup
    │   │   └── UAVMarker.jsx       ← UAV marker + dashed coverage Circle
    │   │
    │   ├── victims/
    │   │   ├── VictimTable.jsx     ← sortable priority table, highlights P1/P2 rows
    │   │   ├── VictimRow.jsx       ← single row: priority badge, vitals, severity bar
    │   │   └── VictimDetail.jsx    ← modal/panel: charts + alert history for one device
    │   │
    │   ├── alerts/
    │   │   ├── AlertFeed.jsx       ← scrollable live feed, newest at top
    │   │   └── AlertRow.jsx        ← single alert: icon, severity color, message, ack button
    │   │
    │   ├── charts/
    │   │   ├── HeartRateChart.jsx  ← Recharts LineChart for heart_rate over time
    │   │   ├── TemperatureChart.jsx ← Recharts LineChart for temperature over time
    │   │   ├── AlertFrequency.jsx  ← Recharts BarChart: alerts per 5-min bin
    │   │   └── PriorityPie.jsx     ← Recharts PieChart: P1/P2/P3 count distribution
    │   │
    │   ├── uavs/
    │   │   ├── UAVGrid.jsx         ← responsive grid of UAV cards
    │   │   └── UAVCard.jsx         ← individual UAV: status, battery bar, stats
    │   │
    │   ├── metrics/
    │   │   ├── MetricStrip.jsx     ← four metric cards across the top of Overview
    │   │   └── MetricCard.jsx      ← single card: label, large value, subtitle
    │   │
    │   └── simulation/
    │       ├── ScenarioPanel.jsx   ← scenario trigger buttons + status
    │       └── ScenarioButton.jsx  ← individual scenario button with loading state
    │
    ├── api/                        ← All HTTP fetch calls in one place
    │   ├── victims.js              ← fetchVictims(), fetchVictimTelemetry(id)
    │   ├── alerts.js               ← fetchAlerts(), acknowledgeAlert(id)
    │   ├── uavs.js                 ← fetchUAVs()
    │   ├── analytics.js            ← fetchSummary(), fetchTimeseries()
    │   └── simulation.js           ← triggerScenario(name), pauseSimulator(), resumeSimulator()
    │
    └── utils/
        ├── priorityColors.js       ← P1 → red, P2 → orange, P3 → green (single source of truth)
        ├── formatters.js           ← formatTimestamp(), formatRSSI(), formatBattery()
        └── constants.js            ← MAP_CENTER, DEFAULT_ZOOM, WS_URL, API_BASE_URL
```

### Frontend architecture rule
> **Pages compose components. Components consume context via hooks. The `api/` folder is the only place that calls `fetch()`. Components never call fetch() directly — they receive data via props or context.**

---

## Simulator structure

```
simulator/
│
├── Dockerfile                      ← runs the simulator as a Docker service
├── requirements.txt                ← paho-mqtt, numpy, python-dotenv
├── config.py                       ← DEVICE_IDS, UAV_IDS, EMIT_INTERVAL,
│                                      ZONE_CENTER, ZONE_RADIUS, MQTT_HOST
├── device_model.py                 ← DeviceState class: current vitals, baseline,
│                                      evolve() method for each tick
├── uav_model.py                    ← UAVState class: position, battery, status
├── scenarios.py                    ← trigger_sos(), trigger_mass_casualty(),
│                                      trigger_uav_failure(), trigger_deterioration(),
│                                      trigger_network_partition()
└── simulator.py                    ← main loop: tick all devices, publish to MQTT,
                                       check for control commands
```

---

## Mosquitto structure

```
mosquitto/
├── mosquitto.conf                  ← listener 1883, allow_anonymous true, logging config
└── data/                           ← mosquitto persistence (created at runtime)
```

---

## Docker Compose service map

```yaml
# How services connect:

postgres:
  image: postgres:15-alpine
  ports: 5432:5432
  volumes: postgres_data:/var/lib/postgresql/data
  # backend connects via DATABASE_URL=postgresql://aegis:password@postgres:5432/aegisdb

mosquitto:
  image: eclipse-mosquitto:2
  ports: 1883:1883
  volumes: ./mosquitto/mosquitto.conf
  # simulator connects via MQTT_HOST=mosquitto port 1883
  # backend connects via MQTT_HOST=mosquitto port 1883

backend:
  build: ./backend
  ports: 8000:8000
  depends_on: [postgres, mosquitto]
  env_file: .env
  # frontend proxies /api/* and /ws → http://backend:8000

simulator:
  build: ./simulator
  depends_on: [mosquitto]
  env_file: .env
  # no ports exposed — only publishes to MQTT

frontend:
  build: ./frontend
  ports: 3000:80
  depends_on: [backend]
  # development: Vite dev server with proxy config
  # production: nginx serving built React app
```

### Service communication — internal Docker DNS
Inside Docker Compose, services refer to each other by **service name**, not localhost:
- Backend connects to Postgres at: `postgresql://aegis:password@postgres:5432/aegisdb`
- Simulator connects to MQTT at: `mqtt://mosquitto:1883`
- Backend connects to MQTT at: `mosquitto` port `1883`
- Frontend (in browser) connects to backend at: `http://localhost:8000` (via Vite proxy in dev)

> **Common mistake**: using `localhost` inside Docker containers. `localhost` inside a container refers to that container itself, not the host machine or other services. Always use the service name.
