import { useWebSocketContext } from '../contexts/WebSocketContext'
import UAVCard from '../components/uavs/UAVCard'
import { muted, pageTitle } from '../utils/themeClasses'
import { REGIONS, REGION_KEYS } from '../utils/regions'

export default function UAVFleetPage() {
  const { uavs, region, setRegion } = useWebSocketContext()
  const sorted = [...uavs].sort((a, b) => a.uav_id.localeCompare(b.uav_id))

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h2 className={pageTitle}>UAV Fleet — {REGIONS[region]?.label}</h2>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="rounded border border-slate-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
        >
          {REGION_KEYS.map((k) => (
            <option key={k} value={k}>{REGIONS[k].label}</option>
          ))}
        </select>
      </div>

      {sorted.length === 0 ? (
        <p className={`${muted} text-center py-20`}>No UAVs in this region yet.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {sorted.map((uav) => (
            <UAVCard key={uav.uav_id} uav={uav} />
          ))}
        </div>
      )}
    </div>
  )
}
