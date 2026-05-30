# API_FLOW.md — Data Flow and API Reference

> This document defines every API endpoint, the WebSocket protocol, and the complete lifecycle of a telemetry packet from the moment the simulator publishes it to when it appears on the React dashboard.

---

## Complete telemetry lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  SIMULATOR (Python)                                             │
│                                                                 │
│  Every 5 seconds, for each of 15–20 devices:                   │
│  1. Evolve device state (add noise, drift GPS)                  │
│  2. Build JSON payload                                          │
│  3. mqtt_client.publish("lorawan/WB-007/uplink", payload_json) │
└────────────────────────┬────────────────────────────────────────┘
                         │ MQTT publish (port 1883)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  MOSQUITTO BROKER                                               │
│                                                                 │
│  Routes message to all subscribers of "lorawan/+/uplink"       │
└────────────────────────┬────────────────────────────────────────┘
                         │ MQTT deliver to subscriber
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASTAPI — mqtt_client.py (on_message callback)                 │
│                                                                 │
│  Step 1: Parse JSON string → Python dict                        │
│  Step 2: Pydantic validation → TelemetryIn schema               │
│          └─ reject malformed packets (log warning, discard)     │
│  Step 3: preprocessing.py                                       │
│          ├─ deduplicate()  → check last record for this device  │
│          │                   reject if same timestamp ±2s       │
│          ├─ validate_ranges() → HR: 0–220, temp: 30–43          │
│          └─ tag_signal_quality() → RSSI < -100 → poor_signal    │
│  Step 4: ai/__init__.py → run_ai_pipeline(telemetry)            │
│          ├─ triage_scorer.compute_severity_score()              │
│          ├─ triage_scorer.classify_priority()                   │
│          ├─ anomaly_detector.predict()                          │
│          └─ alert_generator.decide_alerts()                     │
│  Step 5: device_service.upsert_device()                         │
│          └─ UPDATE devices SET severity_score=X, last_seen=now  │
│  Step 6: telemetry_service.insert_telemetry()                   │
│          └─ INSERT INTO telemetry VALUES (...)                  │
│  Step 7: alert_service.create_alerts() (for each alert)         │
│          └─ INSERT INTO alerts VALUES (...)                     │
│  Step 8: websocket_manager.broadcast()                          │
│          └─ send JSON to all connected React clients            │
└─────────────────────────────────────────────────────────────────┘
                         │ WebSocket push (ws://localhost:8000/ws)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  REACT DASHBOARD (browser)                                      │
│                                                                 │
│  WebSocketContext receives message                              │
│  Routes by message.type:                                        │
│  ├─ "telemetry_update" → update victim in state array           │
│  │   → VictimTable re-sorts by severity_score                   │
│  │   → VictimMarker updates color on map                        │
│  │   → MetricCards recalculate totals                           │
│  ├─ "alert"           → prepend to alerts array                  │
│  │   → AlertFeed shows new alert at top                         │
│  │   → MetricCard increments open alerts count                  │
│  └─ "uav_update"      → update UAV in state array               │
│      → UAVMarker repositions on map                             │
│      → UAVCard updates battery bar                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## WebSocket protocol

**Endpoint**: `ws://localhost:8000/ws`

**Connection lifecycle**:
1. React app opens connection when root component mounts
2. Backend adds connection to ConnectionManager pool
3. Every processed telemetry packet → backend broadcasts to all connections
4. Client disconnects → backend removes from pool silently (no error)
5. React detects disconnect → attempts reconnect with 3-second delay (up to 5 retries)

**Message format — all messages share this envelope**:
```json
{
  "type": "message_type_string",
  "timestamp": "2025-01-15T14:23:07Z",
  "payload": { }
}
```

**Message types and payloads**:

### type: "telemetry_update"
Sent for every successfully processed and scored telemetry packet.
```json
{
  "type": "telemetry_update",
  "timestamp": "2025-01-15T14:23:07Z",
  "payload": {
    "device_id": "WB-007",
    "latitude": 36.7321,
    "longitude": 3.0841,
    "heart_rate": 42,
    "temperature": 38.9,
    "sos_signal": true,
    "movement": false,
    "rssi": -88,
    "battery": 67,
    "severity_score": 87,
    "priority_class": "P1",
    "is_anomaly": true,
    "anomaly_score": -0.312,
    "status": "sos",
    "uav_relay_id": "UAV-02",
    "last_seen": "2025-01-15T14:23:07Z"
  }
}
```

### type: "alert"
Sent when the alert generator creates a new Alert record.
```json
{
  "type": "alert",
  "timestamp": "2025-01-15T14:23:07Z",
  "payload": {
    "id": 142,
    "device_id": "WB-007",
    "alert_type": "cardiac_anomaly",
    "severity": "critical",
    "message": "WB-007: Critically low heart rate detected (42 bpm). AI confidence: 94%",
    "ai_confidence": 0.94,
    "acknowledged": false
  }
}
```

### type: "uav_update"
Sent every 10 seconds (UAVs update less frequently than wearables).
```json
{
  "type": "uav_update",
  "timestamp": "2025-01-15T14:23:10Z",
  "payload": {
    "uav_id": "UAV-02",
    "latitude": 36.7412,
    "longitude": 3.0923,
    "altitude": 115.0,
    "battery": 38,
    "status": "active",
    "coverage_radius": 800.0,
    "connected_devices": 7,
    "rssi": -71
  }
}
```

### type: "device_status_change"
Sent only when a device's status changes (online → offline, offline → sos, etc.)
```json
{
  "type": "device_status_change",
  "timestamp": "2025-01-15T14:23:15Z",
  "payload": {
    "device_id": "WB-012",
    "previous_status": "online",
    "new_status": "offline",
    "reason": "no_packets_300s"
  }
}
```

---

## REST API endpoints

**Base URL**: `http://localhost:8000`

All responses use standard HTTP status codes:
- `200 OK` — success
- `404 Not Found` — resource doesn't exist
- `422 Unprocessable Entity` — validation error (auto-generated by FastAPI/Pydantic)
- `500 Internal Server Error` — unexpected error

---

### Victims

#### `GET /api/victims`
Returns all devices with current status and latest AI scores. Used for initial page load.

**Query params**: `?status=online` (optional filter: online | offline | sos)

**Response** `200 OK`:
```json
[
  {
    "device_id": "WB-007",
    "status": "sos",
    "severity_score": 87,
    "priority_class": "P1",
    "is_anomaly": true,
    "latitude": 36.7321,
    "longitude": 3.0841,
    "heart_rate": 42,
    "temperature": 38.9,
    "sos_signal": true,
    "movement": false,
    "rssi": -88,
    "battery": 67,
    "uav_relay_id": "UAV-02",
    "last_seen": "2025-01-15T14:23:07Z"
  }
]
```

#### `GET /api/victims/{device_id}/telemetry`
Returns telemetry history for one device. Used for the victim detail charts.

**Query params**: `?limit=50` (default 50, max 200)

**Response** `200 OK`:
```json
{
  "device_id": "WB-007",
  "readings": [
    {
      "timestamp": "2025-01-15T14:23:07Z",
      "heart_rate": 42,
      "temperature": 38.9,
      "rssi": -88,
      "severity_score": 87,
      "is_anomaly": true
    }
  ]
}
```

---

### Alerts

#### `GET /api/alerts`
Returns recent alerts for the alert feed.

**Query params**:
- `?limit=50` (default 50)
- `?severity=critical` (optional filter: critical | warning | info)
- `?acknowledged=false` (optional filter)

**Response** `200 OK`:
```json
[
  {
    "id": 142,
    "device_id": "WB-007",
    "alert_type": "cardiac_anomaly",
    "severity": "critical",
    "message": "WB-007: Critically low heart rate detected (42 bpm). AI confidence: 94%",
    "ai_confidence": 0.94,
    "acknowledged": false,
    "timestamp": "2025-01-15T14:23:07Z"
  }
]
```

#### `PATCH /api/alerts/{alert_id}/acknowledge`
Marks a single alert as acknowledged.

**Request body**: none required

**Response** `200 OK`:
```json
{
  "id": 142,
  "acknowledged": true,
  "acknowledged_at": "2025-01-15T14:25:00Z"
}
```

---

### UAVs

#### `GET /api/uavs`
Returns current position and status of all simulated UAVs.

**Response** `200 OK`:
```json
[
  {
    "uav_id": "UAV-01",
    "latitude": 36.7412,
    "longitude": 3.0923,
    "altitude": 115.0,
    "battery": 38,
    "status": "active",
    "coverage_radius": 800.0,
    "connected_devices": 7,
    "rssi": -71,
    "timestamp": "2025-01-15T14:23:10Z"
  }
]
```

---

### Analytics

#### `GET /api/analytics/summary`
Returns aggregated summary statistics for the analytics page cards.

**Response** `200 OK`:
```json
{
  "total_victims": 18,
  "victims_by_priority": { "P1": 3, "P2": 7, "P3": 8 },
  "victims_by_status": { "online": 15, "offline": 2, "sos": 1 },
  "total_alerts_last_hour": 24,
  "alerts_by_type": {
    "cardiac_anomaly": 5,
    "sos": 2,
    "no_movement": 8,
    "connectivity_loss": 7,
    "uav_battery": 2
  },
  "avg_heart_rate": 84.3,
  "avg_temperature": 37.1,
  "uavs_online": 4,
  "network_coverage_pct": 87
}
```

#### `GET /api/analytics/timeseries`
Returns alert counts binned into 5-minute intervals for the last 60 minutes.

**Response** `200 OK`:
```json
{
  "bins": [
    { "timestamp": "2025-01-15T13:25:00Z", "count": 2, "critical_count": 1 },
    { "timestamp": "2025-01-15T13:30:00Z", "count": 5, "critical_count": 3 }
  ]
}
```

**SQL behind this endpoint** (explain in thesis):
```sql
SELECT
  date_trunc('minute', timestamp) - 
    (EXTRACT(MINUTE FROM timestamp)::int % 5) * interval '1 minute' AS bin,
  COUNT(*) AS count,
  COUNT(*) FILTER (WHERE severity = 'critical') AS critical_count
FROM alerts
WHERE timestamp > NOW() - INTERVAL '60 minutes'
GROUP BY bin
ORDER BY bin;
```

---

### Simulation control

#### `POST /api/simulation/scenario`
Triggers a named emergency scenario in the simulator.

**Request body**:
```json
{
  "scenario": "mass_casualty"
}
```

**Accepted scenario values**:
- `sos_wave` — 3 random devices activate SOS
- `mass_casualty` — 5 devices drop to critical vitals simultaneously
- `uav_failure` — one random UAV goes offline
- `gradual_deterioration` — one device's HR trends toward dangerous range over 5 minutes
- `network_partition` — one zone loses connectivity for 2 minutes

**Response** `200 OK`:
```json
{
  "scenario": "mass_casualty",
  "triggered_at": "2025-01-15T14:25:00Z",
  "affected_devices": ["WB-003", "WB-009", "WB-011", "WB-014", "WB-017"]
}
```

#### `POST /api/simulation/pause`
Pauses the simulator (stops emitting packets).

**Response** `200 OK`: `{"status": "paused"}`

#### `POST /api/simulation/resume`
Resumes the simulator.

**Response** `200 OK`: `{"status": "running"}`

---

### System

#### `GET /health`
Health check endpoint used by Docker to verify the service is ready.

**Response** `200 OK`:
```json
{
  "status": "ok",
  "database": "connected",
  "mqtt": "connected",
  "uptime_seconds": 3842
}
```

---

## Vite proxy configuration
In development, Vite proxies API and WebSocket requests to avoid CORS issues:

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
}
```

This means React code calls `/api/victims` (relative URL) and Vite transparently forwards it to `http://localhost:8000/api/victims`. No CORS configuration needed in development.

---

## FastAPI CORS configuration
For production builds (nginx serving the React app), FastAPI needs CORS headers:

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
```
