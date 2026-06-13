import { card } from '../../utils/themeClasses'
import { REGIONS } from '../../utils/regions'
import UAVMiniMap from './UAVMiniMap'

const STATUS_COLORS = {
  active:    'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
  standby:   'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400',
  inactive:  'bg-slate-100 text-slate-600 dark:bg-gray-500/20 dark:text-gray-400',
  offline:   'bg-slate-100 text-slate-600 dark:bg-gray-500/20 dark:text-gray-400',
}

export default function UAVCard({ uav }) {
  const battery = uav.battery ?? 0
  const status = uav.status ?? 'standby'
  const badgeClass = STATUS_COLORS[status] ?? STATUS_COLORS.standby
  const regionLabel = REGIONS[uav.current_region || uav.home_region]?.label ?? '—'
  const users = uav.connected_users ?? uav.connected_victims ?? []

  let barColor = 'bg-green-500'
  if (battery < 40) barColor = 'bg-amber-500'
  if (battery < 15) barColor = 'bg-red-500'

  return (
    <div className={`${card} p-4 flex flex-col gap-3`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-bold text-slate-900 dark:text-white">{uav.name || uav.uav_id}</p>
          <p className="text-xs text-slate-500 font-mono">{uav.uav_id}</p>
        </div>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${badgeClass}`}>
          {status.toUpperCase()}
        </span>
      </div>

      <UAVMiniMap uav={uav} users={users} height={160} />

      <div className="h-2 bg-slate-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${battery}%` }} />
      </div>

      <dl className="grid grid-cols-2 gap-y-1 text-xs">
        <div><dt className="text-slate-500">Region</dt><dd className="font-medium">{regionLabel}</dd></div>
        <div><dt className="text-slate-500">Battery</dt><dd className="font-medium">{battery}%</dd></div>
        <div><dt className="text-slate-500">Coords</dt><dd className="font-mono">{uav.latitude?.toFixed(4)}, {uav.longitude?.toFixed(4)}</dd></div>
        <div><dt className="text-slate-500">Coverage</dt><dd>{uav.coverage_radius} m</dd></div>
        <div><dt className="text-slate-500">Users</dt><dd>{uav.connected_devices ?? users.length}</dd></div>
        <div><dt className="text-slate-500">Teams nearby</dt><dd>{uav.nearby_teams ?? 0}</dd></div>
      </dl>

      {users.length > 0 && (
        <ul className="text-xs text-slate-600 dark:text-gray-300 space-y-0.5 border-t border-slate-200 dark:border-gray-700 pt-2">
          {users.map((u) => (
            <li key={u.victim_id}>{u.name || u.victim_id}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
