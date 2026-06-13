import { modalOverlay, modalPanel } from '../../utils/themeClasses'

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

function fmt(value, digits = 1) {
  if (value == null) return '—'
  return typeof value === 'number' ? value.toFixed(digits) : String(value)
}

export default function VictimHistoryModal({ victim, history = [], onClose }) {
  if (!victim) return null

  return (
    <div className={modalOverlay} onClick={onClose}>
      <div
        className={`${modalPanel} w-full max-w-2xl max-h-[85vh] overflow-y-auto p-4`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">Vital History</h2>
            <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
              {victim.name || victim.victim_id} · updates as new packets arrive
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-500 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white text-sm"
            aria-label="Close history"
          >
            ✕
          </button>
        </div>

        {history.length === 0 ? (
          <p className="text-xs text-slate-500 dark:text-gray-500 py-6 text-center">
            No history yet. Values will appear here as telemetry updates arrive.
          </p>
        ) : (
          <div className="rounded border border-slate-200 dark:border-gray-600 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 dark:bg-gray-700/60 text-slate-500 dark:text-gray-400">
                <tr>
                  <th className="px-2 py-2">Time</th>
                  <th className="px-2 py-2">HR</th>
                  <th className="px-2 py-2">Temp</th>
                  <th className="px-2 py-2">SpO₂</th>
                  <th className="px-2 py-2">RR</th>
                  <th className="px-2 py-2">Priority</th>
                  <th className="px-2 py-2">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-gray-700/60">
                {history.map((row, i) => (
                  <tr key={`${row.timestamp}-${i}`} className="text-slate-800 dark:text-gray-200">
                    <td className="px-2 py-2 tabular-nums">{formatTime(row.timestamp)}</td>
                    <td className="px-2 py-2">{fmt(row.heart_rate)}</td>
                    <td className="px-2 py-2">{fmt(row.temperature)}</td>
                    <td className="px-2 py-2">{fmt(row.spo2)}</td>
                    <td className="px-2 py-2">{fmt(row.respiratory_rate)}</td>
                    <td className="px-2 py-2 font-medium">{row.priority_class ?? '—'}</td>
                    <td className="px-2 py-2">{row.severity_score ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
