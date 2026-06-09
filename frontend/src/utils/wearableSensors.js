/**
 * Normalizes victim_sensors assignments into physical wearables for the UI.
 * Excludes coordinator/network fields (rssi, battery) and merges GPS into one unit.
 */

/** Not physical body-worn sensors — shown in coordinator summary only. */
export const COORDINATOR_FIELDS = new Set(['rssi', 'battery'])

/** Merged into a single GPS wearable. */
export const GPS_FIELDS = new Set(['gps_lat', 'gps_lon'])

/** Human-readable labels for physical wearables. */
export const WEARABLE_LABELS = {
  heart_rate: 'Heart Rate Monitor',
  spo2: 'SpO₂ Sensor',
  temperature: 'Temperature Sensor',
  blood_pressure_systolic: 'BP Monitor (Systolic)',
  blood_pressure_diastolic: 'BP Monitor (Diastolic)',
  respiratory_rate: 'Respiratory Sensor',
  motion_activity: 'Motion Sensor',
  fall_detected: 'Fall Detector',
  glucose: 'Glucose Monitor',
  ecg_hr_variability: 'ECG Sensor',
  eeg_alert_index: 'EEG Sensor',
  gps: 'GPS Tracker',
}

/** Maps wearable id → victim state field used to infer data presence. */
export const WEARABLE_VITAL_MAP = {
  heart_rate: 'heart_rate',
  spo2: 'spo2',
  temperature: 'temperature',
  blood_pressure_systolic: 'blood_pressure_systolic',
  blood_pressure_diastolic: 'blood_pressure_diastolic',
  respiratory_rate: 'respiratory_rate',
  glucose: 'glucose',
  ecg_hr_variability: 'ecg_hr_variability',
  eeg_alert_index: 'eeg_alert_index',
  motion_activity: 'motion_activity',
  fall_detected: 'fall_detected',
  gps: 'gps_lat',
}

/**
 * Converts raw assigned_sensors array into deduplicated physical wearables.
 * @returns {Array<{ id: string, label: string }>}
 */
export function normalizeWearables(assignedSensors = []) {
  const seen = new Set()
  const wearables = []
  let hasGps = false

  for (const rawId of assignedSensors) {
    if (COORDINATOR_FIELDS.has(rawId)) continue
    if (GPS_FIELDS.has(rawId)) {
      hasGps = true
      continue
    }
    if (seen.has(rawId)) continue
    seen.add(rawId)
    wearables.push({
      id: rawId,
      label: WEARABLE_LABELS[rawId] || rawId,
    })
  }

  if (hasGps && !seen.has('gps')) {
    wearables.push({ id: 'gps', label: WEARABLE_LABELS.gps })
  }

  return wearables
}

/**
 * Resolves wearable connectivity status from packet sensor_statuses or vital presence.
 */
export function resolveWearableStatus(wearableId, victim, sensorStatuses = {}) {
  if (wearableId === 'gps') {
    const latStatus = sensorStatuses.gps_lat
    const lonStatus = sensorStatuses.gps_lon
    if (latStatus || lonStatus) {
      const bad = [latStatus, lonStatus].some((s) => s && s !== 'active' && s !== 'degraded')
      return bad ? (latStatus || lonStatus) : 'active'
    }
    return victim?.gps_lat != null ? 'active' : 'disconnected'
  }

  const packetStatus = sensorStatuses[wearableId]
  if (packetStatus) return packetStatus

  const vitalKey = WEARABLE_VITAL_MAP[wearableId]
  if (vitalKey && victim?.[vitalKey] != null) return 'active'
  return 'disconnected'
}

/**
 * Resolves per-wearable battery % from sensor_batteries map (simulator) if available.
 */
export function resolveWearableBattery(wearableId, sensorBatteries = {}) {
  if (wearableId === 'gps') {
    return sensorBatteries.gps_lat ?? sensorBatteries.gps_lon ?? null
  }
  return sensorBatteries[wearableId] ?? null
}
