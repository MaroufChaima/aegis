import { useWebSocketContext } from '../contexts/WebSocketContext'
import UAVCard from '../components/uavs/UAVCard'

/**
 * UAVFleetPage — live grid of all simulated UAVs.
 *
 * Reads the uavs array from WebSocketContext (seeded via REST, then kept
 * current by uav_update WebSocket messages).  Renders one UAVCard per UAV
 * sorted alphabetically by uav_id.
 */
export default function UAVFleetPage() {
  const { uavs } = useWebSocketContext()

  const sorted = [...uavs].sort((a, b) => a.uav_id.localeCompare(b.uav_id))

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-white">UAV Fleet</h2>
        <span className="text-sm text-gray-400">{sorted.length} unit{sorted.length !== 1 ? 's' : ''} tracked</span>
      </div>

      {sorted.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-20">
          Waiting for UAV telemetry…
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sorted.map((uav) => (
            <UAVCard key={uav.uav_id} uav={uav} />
          ))}
        </div>
      )}
    </div>
  )
}
