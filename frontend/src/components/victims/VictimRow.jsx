import React from 'react'
import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'

const ROW_BG = {
  P1: 'bg-red-50 dark:bg-red-900/40',
  P2: 'bg-amber-50 dark:bg-amber-900/30',
}

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

export default function VictimRow({ victim, onClick }) {
  const priority = victim.status === 'offline' ? 'offline' : (victim.priority_class ?? 'P3')
  const color = getPriorityColor(priority)
  const rowBg = ROW_BG[victim.priority_class] ?? ''

  const profileColors =
    PROFILE_COLORS[victim.risk_category] || PROFILE_COLORS.unknown

  return (
    <tr
      className={`${rowBg} hover:bg-slate-100 dark:hover:bg-gray-700/50 transition-colors ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <td className="px-4 py-3">
        <span
          className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
          style={{ backgroundColor: color.hex }}
        >
          {priority}
        </span>
      </td>

      <td className="px-4 py-3">
        <div className="font-medium text-slate-900 dark:text-white">
          {victim.name || victim.victim_id}
          {victim.risk_category && (
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium border ml-1 ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}
            >
              {victim.risk_category}
            </span>
          )}
        </div>
        {victim.name && victim.victim_id && (
          <div className="text-xs text-slate-500 dark:text-gray-400 font-mono mt-0.5">
            {victim.victim_id}
          </div>
        )}
      </td>

      <td className={`px-4 py-3 ${
        victim.heart_rate != null && (victim.heart_rate < 50 || victim.heart_rate > 120)
          ? 'text-red-600 dark:text-red-400 font-semibold'
          : ''
      }`}>
        {victim.heart_rate != null ? `${victim.heart_rate.toFixed(1)} bpm` : '—'}
      </td>

      <td className={`px-4 py-3 ${
        victim.temperature != null && victim.temperature > 38.5
          ? 'text-red-600 dark:text-red-400 font-semibold'
          : ''
      }`}>
        {victim.temperature != null ? `${victim.temperature.toFixed(1)} °C` : '—'}
      </td>

      <td className="px-4 py-3">
        {victim.sos_active ? (
          <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white animate-pulse">
            SOS
          </span>
        ) : (
          <span className="text-slate-400 dark:text-gray-500">—</span>
        )}
      </td>

      <td className="px-4 py-3 text-slate-500 dark:text-gray-400 tabular-nums">
        {formatTime(victim.last_seen)}
      </td>

      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-16 bg-slate-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full"
              style={{
                width: `${victim.severity_score ?? 0}%`,
                backgroundColor: color.hex,
              }}
            />
          </div>
          <span className="tabular-nums text-xs">{victim.severity_score ?? 0}</span>
        </div>
      </td>
    </tr>
  )
}
