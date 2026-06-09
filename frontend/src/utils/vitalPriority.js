/** Vital sign definitions — physiological readings only (no network/coordinator fields). */
export const VITAL_DEFS = {
  heart_rate: {
    label: 'Heart Rate',
    unit: 'bpm',
    format: (v) => v.toFixed(1),
    isAlert: (v) => v < 50 || v > 120,
  },
  temperature: {
    label: 'Temperature',
    unit: '°C',
    format: (v) => v.toFixed(1),
    isAlert: (v) => v > 38.5,
  },
  spo2: {
    label: 'SpO₂',
    unit: '%',
    format: (v) => v.toFixed(1),
    isAlert: (v) => v < 94,
  },
  respiratory_rate: {
    label: 'Resp. Rate',
    unit: 'br/min',
    format: (v) => v.toFixed(1),
    isAlert: (v) => v < 10 || v > 25,
  },
  blood_pressure_systolic: {
    label: 'BP Systolic',
    unit: 'mmHg',
    format: (v) => v.toFixed(0),
    isAlert: (v) => v < 80 || v > 160,
  },
  blood_pressure_diastolic: {
    label: 'BP Diastolic',
    unit: 'mmHg',
    format: (v) => v.toFixed(0),
    isAlert: (v) => v < 50 || v > 100,
  },
  glucose: {
    label: 'Glucose',
    unit: 'mg/dL',
    format: (v) => v.toFixed(0),
    isAlert: (v) => v < 70 || v > 180,
  },
  ecg_hr_variability: {
    label: 'ECG HRV',
    unit: 'ms',
    format: (v) => v.toFixed(1),
    isAlert: () => false,
  },
  eeg_alert_index: {
    label: 'EEG Alert Index',
    unit: '',
    format: (v) => v.toFixed(2),
    isAlert: (v) => v > 0.7,
  },
  motion_activity: {
    label: 'Motion Activity',
    unit: '',
    format: (v) => v.toFixed(2),
    isAlert: () => false,
  },
  fall_detected: {
    label: 'Fall Detected',
    unit: '',
    format: (v) => (v ? 'Yes' : 'No'),
    isAlert: (v) => v > 0,
  },
}

/** Base order per risk category — specialized vitals appended separately. */
export const CONDITION_VITAL_ORDER = {
  diabetic: ['glucose', 'heart_rate', 'blood_pressure_systolic', 'spo2', 'temperature', 'respiratory_rate', 'blood_pressure_diastolic'],
  cardiac: ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'spo2', 'respiratory_rate', 'temperature'],
  elderly: ['heart_rate', 'blood_pressure_systolic', 'spo2', 'temperature', 'respiratory_rate', 'blood_pressure_diastolic'],
  child: ['heart_rate', 'respiratory_rate', 'temperature', 'spo2', 'blood_pressure_systolic', 'blood_pressure_diastolic'],
  pregnant: ['blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'respiratory_rate', 'spo2', 'temperature'],
  neurological: ['eeg_alert_index', 'heart_rate', 'respiratory_rate', 'spo2', 'temperature', 'blood_pressure_systolic'],
  athlete: ['heart_rate', 'respiratory_rate', 'spo2', 'temperature', 'blood_pressure_systolic', 'ecg_hr_variability'],
  healthy: ['heart_rate', 'temperature', 'spo2', 'respiratory_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic'],
}

export const CONDITION_AWARENESS = {
  diabetic: 'Prioritize glucose monitoring — victim is diabetic. Watch for hypo/hyperglycemia.',
  cardiac: 'Monitor heart rate and blood pressure closely — cardiac history.',
  elderly: 'Watch heart rate and blood pressure — elderly victim with higher baseline risk.',
  child: 'Prioritize heart rate and respiratory rate — pediatric victim.',
  pregnant: 'Monitor blood pressure and heart rate closely — pregnant victim.',
  neurological: 'Watch EEG alert index and breathing patterns — neurological condition.',
  athlete: 'Athlete baseline differs from general population — use personalized thresholds.',
}

const SPECIALIZED_VITALS = ['glucose', 'ecg_hr_variability', 'eeg_alert_index']

/**
 * Returns all vital keys to display, ordered by risk profile and assigned sensors.
 */
export function getOrderedVitalKeys(riskCategory, assignedSensors = []) {
  const baseOrder = CONDITION_VITAL_ORDER[riskCategory] || CONDITION_VITAL_ORDER.healthy
  const allKeys = Object.keys(VITAL_DEFS)

  const fromProfile = SPECIALIZED_VITALS.filter((k) => assignedSensors.includes(k))
  const standard = [
    'heart_rate', 'temperature', 'spo2', 'respiratory_rate',
    'blood_pressure_systolic', 'blood_pressure_diastolic',
    'motion_activity', 'fall_detected',
  ]

  const candidateSet = new Set([...baseOrder, ...fromProfile, ...standard])
  const prioritized = baseOrder.filter((k) => candidateSet.has(k))
  const rest = [...candidateSet].filter((k) => allKeys.includes(k) && !prioritized.includes(k))

  return [...prioritized, ...rest.filter((k) => allKeys.includes(k))]
}

export function getPriorityVitalKeys(riskCategory, assignedSensors = []) {
  const ordered = getOrderedVitalKeys(riskCategory, assignedSensors)
  return ordered.slice(0, 2)
}

export function getAwarenessNote(riskCategory) {
  if (!riskCategory || riskCategory === 'healthy') return null
  return CONDITION_AWARENESS[riskCategory] || null
}
