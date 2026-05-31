// Geographic centre of the simulated disaster zone (Algiers region)
// Matches ZONE_CENTER in simulator/config.py
export const MAP_CENTER = [36.7321, 3.0841]

// Default Leaflet zoom level — shows roughly a 4 km radius
export const DEFAULT_ZOOM = 14

// Backend base URL — in dev, Vite proxies /api/* here automatically
export const API_BASE_URL = 'http://localhost:8000'

// WebSocket endpoint — proxied by Vite from /ws to ws://localhost:8000/ws
export const WS_URL = 'ws://localhost:8000/ws'
