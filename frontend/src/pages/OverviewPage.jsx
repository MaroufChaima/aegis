import { useEffect, useState } from 'react'
import ZoneMap from '../components/map/ZoneMap'
import VictimTable from '../components/victims/VictimTable'
import { fetchVictims } from '../api/victims'

/**
 * OverviewPage — primary operator view.
 *
 * Fetches the current device list on mount and passes it to both the
 * zone map and the priority table. Real-time updates will be layered
 * on top via WebSocket in a later phase.
 */
export default function OverviewPage() {
  const [victims, setVictims] = useState([])
  const [error, setError]     = useState(null)

  useEffect(() => {
    fetchVictims()
      .then(setVictims)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
          Could not load devices: {error}
        </div>
      )}

      {/* Zone map */}
      <div className="h-[480px] rounded-lg overflow-hidden border border-gray-700">
        <ZoneMap victims={victims} />
      </div>

      {/* Priority table */}
      <VictimTable victims={victims} />

      <p className="text-gray-500 text-xs">{victims.length} device(s) — refreshed on load</p>
    </div>
  )
}
