import VictimRow from './VictimRow'
import { tableBody, tableDivide, tableHead, tableWrap } from '../../utils/themeClasses'

/**
 * VictimTable — sortable priority table of all registered devices.
 */
export default function VictimTable({ victims = [], onRowClick }) {
  const sorted = [...victims].sort((a, b) => (b.severity_score ?? 0) - (a.severity_score ?? 0))

  return (
    <div className={tableWrap}>
      <table className={`w-full ${tableBody}`}>
        <thead className={tableHead}>
          <tr>
            <th className="px-4 py-3">Priority</th>
            <th className="px-4 py-3">Victim</th>
            <th className="px-4 py-3">Heart Rate</th>
            <th className="px-4 py-3">Temperature</th>
            <th className="px-4 py-3">SOS</th>
            <th className="px-4 py-3">Last Seen</th>
            <th className="px-4 py-3">Score</th>
          </tr>
        </thead>
        <tbody className={tableDivide}>
          {sorted.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-6 text-center text-slate-500 dark:text-gray-500">
                No devices registered yet
              </td>
            </tr>
          )}
          {sorted.map((victim) => (
            <VictimRow
              key={victim.victim_id}
              victim={victim}
              onClick={onRowClick ? () => onRowClick(victim) : undefined}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
