import { PROFILE_COLORS } from '../../utils/constants'
import { resolveAlertThresholds } from '../../utils/personalThresholds'

/**
 * Displays personalized physiological normal ranges for one victim profile.
 */
export default function ProfileRangesPanel({ profile }) {
  if (!profile) return null

  const category = profile.risk_category || 'unknown'
  const colors = PROFILE_COLORS[category] || PROFILE_COLORS.unknown

  const alertT = resolveAlertThresholds(profile) || {}

  const alertLabel = (key) => {
    const t = alertT[key]
    if (!t) return null
    const parts = []
    if (t.low != null) parts.push(`<${t.low.toFixed(1)}`)
    if (t.high != null) parts.push(`>${t.high.toFixed(1)}`)
    return parts.length ? parts.join(' or ') : null
  }

  const ranges = [
    profile.hr_normal_min != null && {
      label: 'Heart Rate',
      range: `${profile.hr_normal_min}–${profile.hr_normal_max} bpm`,
      alert: alertLabel('heart_rate'),
      baseline: profile.hr_baseline != null ? `baseline ${profile.hr_baseline} bpm` : null,
    },
    profile.temp_normal_min != null && {
      label: 'Temperature',
      range: `${profile.temp_normal_min}–${profile.temp_normal_max} °C`,
      alert: alertLabel('temperature'),
    },
    profile.spo2_normal_min != null && {
      label: 'SpO₂',
      range: `≥ ${profile.spo2_normal_min}%`,
      alert: alertLabel('spo2'),
    },
    profile.rr_normal_min != null && {
      label: 'Respiratory Rate',
      range: `${profile.rr_normal_min}–${profile.rr_normal_max} br/min`,
      alert: alertLabel('respiratory_rate'),
    },
    profile.bp_systolic_normal_min != null && {
      label: 'BP Systolic',
      range: `${profile.bp_systolic_normal_min}–${profile.bp_systolic_normal_max} mmHg`,
      alert: alertLabel('blood_pressure_systolic'),
    },
    profile.glucose_normal_min != null && {
      label: 'Glucose',
      range: `${profile.glucose_normal_min}–${profile.glucose_normal_max} mg/dL`,
      alert: alertLabel('glucose'),
    },
  ].filter(Boolean)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colors.bg} ${colors.text} ${colors.border}`}
        >
          {category}
        </span>
        <span className="text-sm font-semibold text-white">
          {profile.name || profile.victim_id}
        </span>
      </div>

      <p className="text-xs text-gray-400">
        These ranges are personalized for this victim&apos;s medical profile.
        Values outside these bounds may trigger alerts even when they look normal
        for the general population.
      </p>

      {profile.notes && (
        <p className="text-xs text-blue-200/90 bg-blue-900/30 border border-blue-700/40 rounded px-2 py-1.5">
          {profile.notes}
        </p>
      )}

      <div className="rounded border border-gray-600 overflow-hidden">
        <div className="grid grid-cols-3 gap-x-3 gap-y-0 px-3 py-2 bg-gray-700/60 text-xs text-gray-400 font-medium">
          <span>Parameter</span>
          <span>Normal range</span>
          <span>Alert if</span>
        </div>
        {ranges.map((row) => (
          <div
            key={row.label}
            className="grid grid-cols-3 gap-x-3 px-3 py-2 border-t border-gray-700/60 text-xs"
          >
            <span className="text-gray-200">{row.label}</span>
            <div>
              <span className="text-white font-medium">{row.range}</span>
              {row.baseline && (
                <span className="block text-gray-500 mt-0.5">{row.baseline}</span>
              )}
            </div>
            <span className="text-amber-300/90">{row.alert || '—'}</span>
          </div>
        ))}
      </div>

      {profile.assigned_sensor_count > 0 && (
        <p className="text-xs text-gray-500">
          {profile.assigned_sensor_count} sensors assigned to this victim.
        </p>
      )}
    </div>
  )
}
