import { useState, useEffect } from 'react'
import ZoneMap from '../components/map/ZoneMap'
import VictimTable from '../components/victims/VictimTable'
import VictimDetail from '../components/victims/VictimDetail'
import AlertFeed from '../components/alerts/AlertFeed'
import { useWebSocketContext } from '../contexts/WebSocketContext'
import { fetchAllVictimsNew } from '../api/profiles'

/**
 * Extract the trailing integer from an ID string.
 * "WBAN-001" → 1,  "V-001" → 1,  "UAV-3" → 3,  "foo" → null
 */
function extractNum(id = '') {
  const m = id.match(/(\d+)$/)
  return m ? parseInt(m[1], 10) : null
}

/**
 * OverviewPage — primary operator view.
 *
 * Reads victims and alerts from WebSocketContext (device-based system).
 * Also loads /api/victims-new once to enrich each device object with
 * risk_category and victim_id from the WBAN victim table, matched by
 * the numeric suffix of their IDs (WBAN-001 ↔ V-001).
 *
 * Clicking a row opens VictimDetail in a side panel.
 */
export default function OverviewPage() {
  const { victims, alerts } = useWebSocketContext()
  const [selectedVictim, setSelectedVictim] = useState(null)
  const [victimsNew, setVictimsNew] = useState([])

  useEffect(() => {
    fetchAllVictimsNew()
      .then(setVictimsNew)
      .catch(err => console.warn('[OverviewPage] victims-new fetch failed:', err))
  }, [])

  // Merge risk_category + victim_id from the WBAN victims table into the
  // device objects, matched by the numeric suffix of their respective IDs.
  const enrichedVictims = victims.map(device => {
    const n = extractNum(device.device_id)
    const match = n != null ? victimsNew.find(v => extractNum(v.victim_id) === n) : null
    if (!match) return device
    return { ...device, risk_category: match.risk_category, victim_id: match.victim_id }
  })

  // Keep the detail panel in sync as WebSocket updates arrive.
  const liveSelectedVictim = selectedVictim
    ? (enrichedVictims.find(v => v.device_id === selectedVictim.device_id) ?? selectedVictim)
    : null

  return (
    <div className="space-y-6">

      {/* Zone map */}
      <div className="h-[480px] rounded-lg overflow-hidden border border-gray-700">
        <ZoneMap victims={enrichedVictims} />
      </div>

      {/* Priority table + detail panel side-by-side when a victim is selected */}
      <div className={`flex gap-4 items-start ${liveSelectedVictim ? 'flex-col lg:flex-row' : ''}`}>
        <div className={liveSelectedVictim ? 'lg:flex-1 w-full' : 'w-full'}>
          <VictimTable victims={enrichedVictims} onRowClick={setSelectedVictim} />
        </div>

        {liveSelectedVictim && (
          <div className="lg:w-96 w-full flex-shrink-0">
            <VictimDetail
              victim={liveSelectedVictim}
              onClose={() => setSelectedVictim(null)}
            />
          </div>
        )}
      </div>

      {/* Alert feed */}
      <AlertFeed alerts={alerts} />

    </div>
  )
}
