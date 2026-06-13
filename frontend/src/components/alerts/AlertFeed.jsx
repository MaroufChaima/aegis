import AlertRow from './AlertRow'
import { mutedSm } from '../../utils/themeClasses'

export default function AlertFeed({ alerts = [], victims = [] }) {
  const visible = alerts.slice(0, 15)

  const nameById = Object.fromEntries(
    victims
      .filter((v) => v.victim_id)
      .map((v) => [v.victim_id, v.name || v.victim_id]),
  )

  return (
    <section>
      <h2 className={`${mutedSm} font-semibold uppercase tracking-wider mb-2`}>
        Alert Feed
        {alerts.length > 0 && (
          <span className="ml-2 text-xs bg-slate-200 text-slate-600 dark:bg-gray-700 dark:text-gray-300 px-1.5 py-0.5 rounded-full">
            {alerts.length}
          </span>
        )}
      </h2>

      <div className="rounded-lg overflow-hidden border border-slate-200 dark:border-gray-700 divide-y divide-slate-200 dark:divide-gray-700/60 shadow-sm">
        {visible.length === 0 ? (
          <p className="px-4 py-6 text-center text-slate-500 dark:text-gray-500 text-sm">
            No alerts yet
          </p>
        ) : (
          visible.map((alert, i) => (
            <AlertRow
              key={alert.id ?? i}
              alert={alert}
              victimName={nameById[alert.victim_id || alert.device_id]}
            />
          ))
        )}
      </div>
    </section>
  )
}
