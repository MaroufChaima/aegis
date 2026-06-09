import VictimRow from './VictimRow'

/**
 * VictimTable — sortable priority table of all registered devices.
 *
 * Rows are sorted descending by severity_score before render.
 * P1 rows are highlighted red, P2 rows amber.
 * Pass onRowClick to make rows selectable.
 *
 * @param {{ victims: Array, onRowClick: function }} props
 *   victims     — array of device objects from GET /api/victims or WebSocket state
 *   onRowClick  — optional callback fired with the victim object when a row is clicked
 */
export default function VictimTable({ victims = [], onRowClick }) {
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
