/** Profile-specific priority vital for emergency operations queue. */

const MAP = {
  healthy:      { key: 'respiratory_rate', label: 'Resp. Rate', unit: 'br/min', fallback: 'heart_rate' },
  diabetic:     { key: 'glucose', label: 'Glucose', unit: 'mg/dL', fallback: 'heart_rate' },
  cardiac:      { key: 'ecg_hr_variability', label: 'ECG HRV', unit: 'ms', fallback: 'blood_pressure_systolic' },
  neurological: { key: 'eeg_alert_index', label: 'EEG Index', unit: '', fallback: 'respiratory_rate' },
  athlete:      { key: 'respiratory_rate', label: 'Resp. Rate', unit: 'br/min', fallback: 'heart_rate' },
  elderly:      { key: 'spo2', label: 'SpO₂', unit: '%', fallback: 'respiratory_rate' },
  pregnant:     { key: 'blood_pressure_systolic', label: 'BP Sys', unit: 'mmHg', fallback: 'heart_rate' },
  child:        { key: 'heart_rate', label: 'Heart Rate', unit: 'bpm', fallback: 'respiratory_rate' },
}

const LABELS = {
  heart_rate: 'Heart Rate', respiratory_rate: 'Resp. Rate', glucose: 'Glucose',
  ecg_hr_variability: 'ECG HRV', eeg_alert_index: 'EEG Index', spo2: 'SpO₂',
  blood_pressure_systolic: 'BP Sys',
}

const UNITS = {
  heart_rate: 'bpm', respiratory_rate: 'br/min', glucose: 'mg/dL',
  ecg_hr_variability: 'ms', eeg_alert_index: '', spo2: '%', blood_pressure_systolic: 'mmHg',
}

export function getPriorityVital(user) {
  const cat = user?.risk_category || 'healthy'
  const spec = MAP[cat] || MAP.healthy
  let value = user?.[spec.key]
  let key = spec.key
  let label = spec.label
  let unit = spec.unit

  if (value == null && spec.fallback) {
    value = user?.[spec.fallback]
    key = spec.fallback
    label = LABELS[spec.fallback] || spec.fallback
    unit = UNITS[spec.fallback] || ''
  }

  const formatted = value != null
    ? `${typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(1)) : value}${unit ? ` ${unit}` : ''}`
    : '—'

  return { key, label, value, unit, formatted }
}
