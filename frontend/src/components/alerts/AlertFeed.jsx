import AlertRow from './AlertRow'

/**
 * AlertFeed — scrollable list of the most recent alerts, newest at top.
 *
 * Slices the incoming array to the last 15 entries so the feed stays
 * readable regardless of how many alerts the context holds. Actual
 * capping to 100 is handled in WebSocketContext.
 *
 * @param {{ alerts: Array }} props
 *   alerts — array of alert objects from WebSocketContext
 */
export default function AlertFeed({ alerts = [] }) {
  const visible = alerts.slice(0, 15)

  return (
    <section>
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">
        Alert Feed
        {alerts.length > 0 && (
          <span className="ml-2 text-xs bg-gray-700 text-gray-300 px-1.5 py-0.5 rounded-full">
            {alerts.length}
          </span>
        )}
      </h2>

      <div className="rounded-lg overflow-hidden border border-gray-700 divide-y divide-gray-700/60">
        {visible.length === 0 ? (
          <p className="px-4 py-6 text-center text-gray-500 text-sm">
            No alerts yet
          </p>
        ) : (
          visible.map((alert, i) => (
            <AlertRow key={alert.id ?? i} alert={alert} />
          ))
        )}
      </div>
    </section>
  )
}
