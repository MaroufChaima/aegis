// Geographic centre of the simulated disaster zone (Algiers region)
// Matches ZONE_CENTER in simulator/config.py
export const MAP_CENTER = [36.7321, 3.0841]

// Default Leaflet zoom level — shows roughly a 4 km radius
export const DEFAULT_ZOOM = 14

// Backend base URL — in dev, Vite proxies /api/* here automatically
export const API_BASE_URL = 'http://localhost:8000'

// WebSocket endpoint — proxied by Vite from /ws to ws://localhost:8000/ws
export const WS_URL = 'ws://localhost:8000/ws'

// Color classes for victim medical profile badges
export const PROFILE_COLORS = {
  healthy: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  diabetic: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
  cardiac: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
  elderly: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-300' },
  athlete: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
  neurological: { bg: 'bg-indigo-100', text: 'text-indigo-800', border: 'border-indigo-300' },
  pregnant: { bg: 'bg-pink-100', text: 'text-pink-800', border: 'border-pink-300' },
  child: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
  unknown: { bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-300' }
}

// Human-readable names for sensor type IDs
export const SENSOR_LABELS = {
  heart_rate: 'Heart Rate',
  spo2: 'SpO2',
  temperature: 'Temperature',
  blood_pressure_systolic: 'BP Systolic',
  blood_pressure_diastolic: 'BP Diastolic',
  respiratory_rate: 'Resp. Rate',
  motion_activity: 'Motion',
  fall_detected: 'Fall Detect',
  gps_lat: 'GPS Lat',
  gps_lon: 'GPS Lon',
  rssi: 'Signal',
  battery: 'Battery',
  glucose: 'Glucose',
  ecg_hr_variability: 'ECG HRV',
  eeg_alert_index: 'EEG Index'
}

// Units for sensor readings display
export const SENSOR_UNITS = {
  heart_rate: 'bpm',
  spo2: '%',
  temperature: '°C',
  blood_pressure_systolic: 'mmHg',
  blood_pressure_diastolic: 'mmHg',
  respiratory_rate: 'br/min',
  motion_activity: '',
  fall_detected: '',
  rssi: 'dBm',
  battery: '%',
  glucose: 'mg/dL',
  ecg_hr_variability: 'ms',
  eeg_alert_index: ''
}
