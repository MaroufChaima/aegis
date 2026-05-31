import { getPriorityColor } from '../../utils/priorityColors'

/**
 * Row background by priority class.
 * P1 → red tint, P2 → amber tint, P3/offline → transparent.
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
 * VictimTable — sortable priority table of all registered devices.
 *
 * Rows are sorted descending by severity_score before render.
 * P1 rows are highlighted red, P2 rows amber. No click handler.
 *
 * @param {{ victims: Array }} props
 *   victims — array of device objects from GET /api/victims or WebSocket state
 */
export default function VictimTable({ victims = [] }) {
  const sorted = [...victims].sort((a, b) => (b.severity_score ?? 0) - (a.severity_score ?? 0))

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-700">
      <table className="w-full text-sm text-left text-gray-200">
        <thead className="text-xs uppercase bg-gray-800 text-gray-400">
          <tr>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Device ID</th>
            <th className="px-4 py-3">Heart Rate</th>
            <th className="px-4 py-3">Temperature</th>
            <th className="px-4 py-3">SOS</th>
            <th className="px-4 py-3">Last Seen</th>
            <th className="px-4 py-3">Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {sorted.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-6 text-center text-gray-500">
                No devices registered yet
              </td>
            </tr>
          )}
          {sorted.map((victim) => {
            const priority = victim.status === 'offline' ? 'offline' : (victim.priority_class ?? 'P3')
            const color = getPriorityColor(priority)
            const rowBg = ROW_BG[victim.priority_class] ?? ''

            return (
              <tr key={victim.device_id} className={`${rowBg} hover:bg-gray-700/50 transition-colors`}>
                {/* Priority badge */}
                <td className="px-4 py-3">
                  <span
                    className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
                    style={{ backgroundColor: color.hex }}
                  >
                    {priority}
                  </span>
                </td>

                <td className="px-4 py-3 font-mono font-medium">{victim.device_id}</td>

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
          })}
        </tbody>
      </table>
    </div>
  )
}
