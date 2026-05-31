/**
 * UAVCard — displays the current state of a single UAV.
 *
 * Shows: UAV ID, status badge, battery bar, altitude, connected devices.
 * Battery bar colour: green ≥ 40 %, amber 15–39 %, red < 15 %.
 *
 * @param {{ uav: object }} props
 */
export default function UAVCard({ uav }) {
  const battery = uav.battery ?? 0
  const status  = uav.status ?? 'unknown'

  const statusColors = {
    active:    'bg-green-500/20 text-green-400 border-green-500/30',
    returning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    offline:   'bg-gray-500/20  text-gray-400  border-gray-500/30',
  }
  const badgeClass = statusColors[status] ?? statusColors.offline

  let barColor = 'bg-green-500'
  if (battery < 40) barColor = 'bg-amber-500'
  if (battery < 15) barColor = 'bg-red-500'

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 flex flex-col gap-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <span className="font-bold text-white text-base tracking-wide">{uav.uav_id}</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${badgeClass}`}>
          {status.toUpperCase()}
        </span>
      </div>

      {/* Battery */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Battery</span>
          <span className={battery < 15 ? 'text-red-400 font-bold' : ''}>{battery}%</span>
        </div>
        <div className="h-2.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${battery}%` }}
          />
        </div>
      </div>

      {/* Stats grid */}
      <dl className="grid grid-cols-2 gap-y-2 text-sm">
        <div>
          <dt className="text-gray-400 text-xs">Altitude</dt>
          <dd className="text-white font-medium">
            {uav.altitude != null ? `${uav.altitude} m` : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-gray-400 text-xs">Devices linked</dt>
          <dd className="text-white font-medium">{uav.connected_devices ?? 0}</dd>
        </div>
        <div>
          <dt className="text-gray-400 text-xs">Coverage</dt>
          <dd className="text-white font-medium">
            {uav.coverage_radius != null ? `${uav.coverage_radius} m` : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-gray-400 text-xs">Last update</dt>
          <dd className="text-gray-300 font-mono text-xs truncate">
            {uav.timestamp ? uav.timestamp.replace('T', ' ').replace('Z', '') : '—'}
          </dd>
        </div>
      </dl>
    </div>
  )
}
