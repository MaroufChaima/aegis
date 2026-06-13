import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'
import { computeBmi, bmiLabel } from '../../utils/bmi'
import { card } from '../../utils/themeClasses'

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

export default function VictimCard({ victim, onClick, selected }) {
  const priority = victim.status === 'offline' ? 'offline' : (victim.priority_class ?? 'P3')
  const color = getPriorityColor(priority)
  const profileColors = PROFILE_COLORS[victim.risk_category] || PROFILE_COLORS.unknown
  const bmi = computeBmi(victim.height_cm, victim.weight_kg)

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${card} p-4 text-left w-full transition-all hover:shadow-md ${
        selected ? 'ring-2 ring-blue-500 dark:ring-blue-400' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <p className="font-semibold text-slate-900 dark:text-white truncate">
            {victim.name || victim.victim_id}
          </p>
          <p className="text-xs text-slate-500 dark:text-gray-400 font-mono">{victim.victim_id}</p>
        </div>
        <span
          className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white flex-shrink-0"
          style={{ backgroundColor: color.hex }}
        >
          {priority}
        </span>
      </div>

      {victim.risk_category && (
        <span
          className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium border mb-3 ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}
        >
          {victim.risk_category}
        </span>
      )}

      <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
        <div>
          <dt className="text-xs text-slate-500 dark:text-gray-400">Heart rate</dt>
          <dd className="font-medium text-slate-900 dark:text-white">
            {victim.heart_rate != null ? `${victim.heart_rate.toFixed(0)} bpm` : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500 dark:text-gray-400">Temp</dt>
          <dd className="font-medium text-slate-900 dark:text-white">
            {victim.temperature != null ? `${victim.temperature.toFixed(1)} °C` : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500 dark:text-gray-400">SpO₂</dt>
          <dd className="font-medium text-slate-900 dark:text-white">
            {victim.spo2 != null ? `${victim.spo2.toFixed(0)}%` : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500 dark:text-gray-400">BMI</dt>
          <dd className="font-medium text-slate-900 dark:text-white text-xs">
            {bmiLabel(bmi)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500 dark:text-gray-400">UAV</dt>
          <dd className="font-medium text-slate-900 dark:text-white text-xs">
            {victim.uav_relay_id ?? '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500 dark:text-gray-400">Score</dt>
          <dd className="font-medium text-slate-900 dark:text-white">{victim.severity_score ?? 0}</dd>
        </div>
      </dl>

      <p className="text-xs text-slate-500 dark:text-gray-500 mt-3">
        Last seen {formatTime(victim.last_seen)}
      </p>
    </button>
  )
}
