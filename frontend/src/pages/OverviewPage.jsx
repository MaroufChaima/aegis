import { useState } from 'react'
import ZoneMap from '../components/map/ZoneMap'
import VictimTable from '../components/victims/VictimTable'
import VictimDetail from '../components/victims/VictimDetail'
import AlertFeed from '../components/alerts/AlertFeed'
import { useWebSocketContext } from '../contexts/WebSocketContext'

/**
 * OverviewPage — primary operator view.
 *
 * Reads victims and alerts from WebSocketContext. GET /api/victims now
 * returns the full WBAN victim_current_state JOIN victims, so no
 * secondary enrichment fetch is needed.
 *
 * Clicking a row opens VictimDetail in a side panel.
 */
export default function OverviewPage() {
  const { victims, alerts } = useWebSocketContext()
  const [selectedVictim, setSelectedVictim] = useState(null)

  // Keep the detail panel in sync as WebSocket updates arrive.
  const liveSelectedVictim = selectedVictim
    ? (victims.find(v => v.victim_id === selectedVictim.victim_id) ?? selectedVictim)
    : null

  return (
    <div className="space-y-6">

      {/* Zone map */}
      <div className="h-[480px] rounded-lg overflow-hidden border border-gray-700">
        <ZoneMap victims={victims} />
      </div>

      {/* Priority table + detail panel side-by-side when a victim is selected */}
      <div className={`flex gap-4 items-start ${liveSelectedVictim ? 'flex-col lg:flex-row' : ''}`}>
        <div className={liveSelectedVictim ? 'lg:flex-1 w-full' : 'w-full'}>
          <VictimTable victims={victims} onRowClick={setSelectedVictim} />
        </div>

        {liveSelectedVictim && (
          <div className="lg:w-96 w-full flex-shrink-0">
            <VictimDetail
              victim={liveSelectedVictim}
              alerts={alerts}
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
