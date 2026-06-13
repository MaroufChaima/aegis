import { PROFILE_COLORS } from '../../utils/constants'

export default function ProfileRangesPanel({ profile }) {
  if (!profile) return null

  const category = profile.risk_category || 'unknown'
  const colors = PROFILE_COLORS[category] || PROFILE_COLORS.unknown
  const ranges = profile.sensor_ranges?.length
    ? profile.sensor_ranges
    : []

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${colors.bg} ${colors.text} ${colors.border}`}>
          {category}
        </span>
        <span className="text-sm font-semibold text-slate-900 dark:text-white">
          {profile.name || profile.victim_id}
        </span>
      </div>

      <p className="text-xs text-slate-500 dark:text-gray-400">
        These ranges are personalized for this user&apos;s medical profile and assigned sensors.
      </p>

      {profile.notes && (
        <p className="text-xs text-blue-800 bg-blue-50 border border-blue-200 rounded px-2 py-1.5 dark:text-blue-200/90 dark:bg-blue-900/30 dark:border-blue-700/40">
          {profile.notes}
        </p>
      )}

      <div className="rounded border border-slate-200 dark:border-gray-600 overflow-hidden max-h-80 overflow-y-auto">
        <div className="grid grid-cols-3 gap-x-3 px-3 py-2 bg-slate-100 dark:bg-gray-700/60 text-xs text-slate-500 dark:text-gray-400 font-medium sticky top-0">
          <span>Parameter</span>
          <span>Normal range</span>
          <span>Alert if</span>
        </div>
        {ranges.length === 0 ? (
          <p className="px-3 py-4 text-xs text-slate-500">No sensor ranges available.</p>
        ) : ranges.map((row) => (
          <div
            key={row.sensor_type_id || row.label}
            className="grid grid-cols-3 gap-x-3 px-3 py-2 border-t border-slate-200 dark:border-gray-700/60 text-xs"
          >
            <span className="text-slate-800 dark:text-gray-200">{row.label}</span>
            <span className="text-slate-900 dark:text-white font-medium">{row.normal_range}</span>
            <span className="text-amber-700 dark:text-amber-300/90">{row.alert_if || '—'}</span>
          </div>
        ))}
      </div>

      {profile.assigned_sensor_count > 0 && (
        <p className="text-xs text-slate-500 dark:text-gray-500">
          {profile.assigned_sensor_count} sensors assigned to this user.
        </p>
      )}
    </div>
  )
}
