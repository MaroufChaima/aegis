import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'
import { getPriorityVital } from '../../utils/priorityVital'
import { isVictimStatus } from '../../utils/userLabel'
import { tableBody, tableDivide, tableHead, tableWrap } from '../../utils/themeClasses'

const PRIORITY_ORDER = { P1: 0, P2: 1, P3: 2, offline: 3 }

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

export default function UserQueue({ users = [], onRowClick, selectedId }) {
  const sorted = [...users].sort((a, b) => {
    const pa = PRIORITY_ORDER[a.priority_class] ?? 2
    const pb = PRIORITY_ORDER[b.priority_class] ?? 2
    if (pa !== pb) return pa - pb
    return (b.severity_score ?? 0) - (a.severity_score ?? 0)
  })

  return (
    <div className={tableWrap}>
      <table className={`w-full ${tableBody} text-sm`}>
        <thead className={tableHead}>
          <tr>
            <th className="px-3 py-2.5 text-left">Priority</th>
            <th className="px-3 py-2.5 text-left">Score</th>
            <th className="px-3 py-2.5 text-left">Name</th>
            <th className="px-3 py-2.5 text-left">Profile</th>
            <th className="px-3 py-2.5 text-left">Critical Vital</th>
            <th className="px-3 py-2.5 text-left">UAV</th>
            <th className="px-3 py-2.5 text-left">Status</th>
          </tr>
        </thead>
        <tbody className={tableDivide}>
          {sorted.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-8 text-center text-slate-500 dark:text-gray-500">
                No users in this region
              </td>
            </tr>
          )}
          {sorted.map((user) => {
            const priority = user.status === 'offline' ? 'offline' : (user.priority_class ?? 'P3')
            const color = getPriorityColor(priority)
            const vital = getPriorityVital(user)
            const profileColors = PROFILE_COLORS[user.risk_category] || PROFILE_COLORS.unknown
            const rowBg = user.priority_class === 'P1'
              ? 'bg-red-50 dark:bg-red-900/30'
              : user.priority_class === 'P2'
                ? 'bg-amber-50 dark:bg-amber-900/20'
                : ''
            const selected = selectedId === user.victim_id

            return (
              <tr
                key={user.victim_id}
                className={`${rowBg} ${selected ? 'ring-1 ring-inset ring-blue-500' : ''} hover:bg-slate-100 dark:hover:bg-gray-700/40 cursor-pointer transition-colors`}
                onClick={() => onRowClick?.(user)}
              >
                <td className="px-3 py-2.5">
                  <span
                    className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
                    style={{ backgroundColor: color.hex }}
                  >
                    {priority}
                  </span>
                </td>
                <td className="px-3 py-2.5 font-mono font-semibold tabular-nums">
                  {user.severity_score ?? 0}
                </td>
                <td className="px-3 py-2.5">
                  <div className="font-medium text-slate-900 dark:text-white">
                    {user.name || user.victim_id}
                    {isVictimStatus(user) && (
                      <span className="ml-1 text-xs font-bold text-red-600 dark:text-red-400">VICTIM</span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-gray-400 font-mono">{user.victim_id}</div>
                </td>
                <td className="px-3 py-2.5">
                  {user.risk_category && (
                    <span className={`inline-flex px-1.5 py-0.5 rounded-full text-xs font-medium border ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}>
                      {user.risk_category}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <span className="text-xs text-slate-500 dark:text-gray-400">{vital.label}</span>
                  <div className="font-semibold text-slate-900 dark:text-white">{vital.formatted}</div>
                </td>
                <td className="px-3 py-2.5 font-mono text-xs">{user.uav_relay_id ?? '—'}</td>
                <td className="px-3 py-2.5 capitalize text-slate-600 dark:text-gray-300">
                  {user.emergency_status === 'victim' ? 'emergency' : (user.status ?? 'online')}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
