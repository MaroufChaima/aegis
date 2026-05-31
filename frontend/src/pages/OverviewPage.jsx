import ZoneMap from '../components/map/ZoneMap'
import VictimTable from '../components/victims/VictimTable'
import AlertFeed from '../components/alerts/AlertFeed'
import { useWebSocketContext } from '../contexts/WebSocketContext'

/**
 * OverviewPage — primary operator view.
 *
 * Reads victims and alerts from WebSocketContext. The provider seeds
 * both arrays from REST on mount, then keeps them live via WebSocket
 * updates. This component owns no state and makes no fetch calls.
 */
export default function OverviewPage() {
  const { victims, alerts } = useWebSocketContext()

  return (
    <div className="space-y-6">

      {/* Zone map */}
      <div className="h-[480px] rounded-lg overflow-hidden border border-gray-700">
        <ZoneMap victims={victims} />
      </div>

      {/* Priority table */}
      <VictimTable victims={victims} />

      {/* Alert feed */}
      <AlertFeed alerts={alerts} />

    </div>
  )
}
