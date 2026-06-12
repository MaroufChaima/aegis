/**
 * Mirrors backend ai/threshold_engine.py resolve_thresholds() for UI consistency.
 * "Normal range" = profile min/max. "Alert threshold" = profile with safety margins.
 */

export function resolveAlertThresholds(profile) {
  if (!profile) return null

  const t = {}
  if (profile.hr_normal_min != null) {
    t.heart_rate = {
      low: profile.hr_normal_min * 0.95,
      high: profile.hr_normal_max * 1.05,
    }
  }
  if (profile.temp_normal_min != null) {
    t.temperature = {
      low: profile.temp_normal_min * 0.98,
      high: profile.temp_normal_max * 1.02,
    }
  }
  if (profile.spo2_normal_min != null) {
    t.spo2 = { low: profile.spo2_normal_min * 0.97, high: null }
  }
  if (profile.rr_normal_min != null) {
    t.respiratory_rate = {
      low: profile.rr_normal_min * 0.90,
      high: profile.rr_normal_max * 1.10,
    }
  }
  if (profile.glucose_normal_min != null) {
    t.glucose = {
      low: profile.glucose_normal_min * 0.90,
      high: profile.glucose_normal_max * 1.10,
    }
  }
  if (profile.bp_systolic_normal_min != null) {
    t.blood_pressure_systolic = {
      low: profile.bp_systolic_normal_min * 0.92,
      high: profile.bp_systolic_normal_max * 1.08,
    }
  }
  return t
}

/**
 * True when value is outside personalized ALERT thresholds (same logic as backend).
 */
export function isOutsidePersonalRange(vitalKey, value, profile, genericIsAlert) {
  if (value == null) return false

  const alert = resolveAlertThresholds(profile)?.[vitalKey]
  if (alert) {
    if (alert.low != null && value < alert.low) return true
    if (alert.high != null && value > alert.high) return true
    return false
  }

  return genericIsAlert?.(value) ?? false
}

function formatBound(v, digits = 1) {
  return Number(v).toFixed(digits)
}

/** Hint showing normal clinical range and when backend alerts fire. */
export function getPersonalRangeHint(vitalKey, profile) {
  if (!profile) return null

  const alert = resolveAlertThresholds(profile)?.[vitalKey]
  let normal = null

  switch (vitalKey) {
    case 'heart_rate':
      if (profile.hr_normal_min != null) {
        normal = `${profile.hr_normal_min}–${profile.hr_normal_max} bpm`
      }
      break
    case 'temperature':
      if (profile.temp_normal_min != null) {
        normal = `${profile.temp_normal_min}–${profile.temp_normal_max} °C`
      }
      break
    case 'spo2':
      if (profile.spo2_normal_min != null) normal = `≥ ${profile.spo2_normal_min}%`
      break
    case 'respiratory_rate':
      if (profile.rr_normal_min != null) {
        normal = `${profile.rr_normal_min}–${profile.rr_normal_max} br/min`
      }
      break
    case 'blood_pressure_systolic':
      if (profile.bp_systolic_normal_min != null) {
        normal = `${profile.bp_systolic_normal_min}–${profile.bp_systolic_normal_max} mmHg`
      }
      break
    case 'glucose':
      if (profile.glucose_normal_min != null) {
        normal = `${profile.glucose_normal_min}–${profile.glucose_normal_max} mg/dL`
      }
      break
    default:
      break
  }

  if (!normal) return null

  if (alert) {
    const parts = []
    if (alert.low != null) parts.push(`<${formatBound(alert.low)}`)
    if (alert.high != null) parts.push(`>${formatBound(alert.high)}`)
    if (parts.length) {
      return `Normal: ${normal} · Alert if ${parts.join(' or ')}`
    }
  }

  return `Normal: ${normal}`
}
