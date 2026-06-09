import React from 'react'
import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'

/**
 * Row background tint by priority class.
 * P1 → red tint, P2 → amber tint, everything else → transparent.
 */
const ROW_BG = {
  P1: 'bg-red-900/40',
  P2: 'bg-amber-900/30',
}

/**
 * Format an ISO timestamp to a short HH:MM:SS local string.
 * Returns '—' if the value is null/undefined.
 */
function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

/**
 * VictimRow — a single table row for one registered device.
 *
 * Displays priority, device ID (with optional profile badge), heart rate,
 * temperature, SOS state, last-seen time, and severity score bar.
 *
 * @param {{ victim: object, onClick: function }} props
 *   victim  — a device object from GET /api/victims or WebSocket state
 *   onClick — optional callback fired when the row is clicked
 */
export default function VictimRow({ victim, onClick }) {
  const priority = victim.status === 'offline' ? 'offline' : (victim.priority_class ?? 'P3')
  const color = getPriorityColor(priority)
  const rowBg = ROW_BG[victim.priority_class] ?? ''

  const profileColors =
    PROFILE_COLORS[victim.risk_category] || PROFILE_COLORS.unknown

  return (
    <tr
      className={`${rowBg} hover:bg-gray-700/50 transition-colors ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      {/* Priority badge */}
      <td className="px-4 py-3">
        <span
          className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
          style={{ backgroundColor: color.hex }}
        >
          {priority}
        </span>
      </td>

      {/* Device ID + optional profile badge */}
      <td className="px-4 py-3 font-mono font-medium">
        {victim.device_id}
        {victim.risk_category && (
          <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium border ml-1 ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}
          >
            {victim.risk_category}
          </span>
        )}
      </td>

      {/* Heart rate — red if out of normal range */}
      <td className={`px-4 py-3 ${
        victim.heart_rate != null && (victim.heart_rate < 50 || victim.heart_rate > 120)
          ? 'text-red-400 font-semibold'
          : ''
      }`}>
        {victim.heart_rate != null ? `${victim.heart_rate} bpm` : '—'}
      </td>

      {/* Temperature — red if elevated */}
      <td className={`px-4 py-3 ${
        victim.temperature != null && victim.temperature > 38.5
          ? 'text-red-400 font-semibold'
          : ''
      }`}>
        {victim.temperature != null ? `${victim.temperature} °C` : '—'}
      </td>

      {/* SOS — red pill when active */}
      <td className="px-4 py-3">
        {victim.sos_signal ? (
          <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white animate-pulse">
            SOS
          </span>
        ) : (
          <span className="text-gray-500">—</span>
        )}
      </td>

      <td className="px-4 py-3 text-gray-400 tabular-nums">
        {formatTime(victim.last_seen)}
      </td>

      {/* Severity score bar */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-16 bg-gray-700 rounded-full h-1.5">
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
