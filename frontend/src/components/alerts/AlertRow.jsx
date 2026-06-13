const SEVERITY = {
  critical: {
    border: 'border-red-500',
    icon:   'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400',
    label:  'text-red-600 dark:text-red-400',
    badge:  'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300',
    symbol: '⚠',
  },
  warning: {
    border: 'border-amber-500',
    icon:   'bg-amber-100 text-amber-700 dark:bg-amber-400/20 dark:text-amber-300',
    label:  'text-amber-700 dark:text-amber-300',
    badge:  'bg-amber-100 text-amber-800 dark:bg-amber-400/20 dark:text-amber-200',
    symbol: '!',
  },
  info: {
    border: 'border-blue-500',
    icon:   'bg-blue-100 text-blue-600 dark:bg-blue-400/20 dark:text-blue-300',
    label:  'text-blue-600 dark:text-blue-300',
    badge:  'bg-blue-100 text-blue-700 dark:bg-blue-400/20 dark:text-blue-200',
    symbol: 'i',
  },
}

const DEFAULT_SEVERITY = {
  border: 'border-slate-300 dark:border-gray-600',
  icon:   'bg-slate-100 text-slate-500 dark:bg-gray-600/20 dark:text-gray-400',
  label:  'text-slate-500 dark:text-gray-400',
  badge:  'bg-slate-100 text-slate-600 dark:bg-gray-600/20 dark:text-gray-300',
  symbol: '•',
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? '' : d.toLocaleTimeString()
}

export default function AlertRow({ alert, victimName }) {
  const style = SEVERITY[alert.severity] ?? DEFAULT_SEVERITY
  const victimId = alert.victim_id || alert.device_id
  const displayName = victimName || victimId

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 border-l-2 ${style.border} bg-white dark:bg-gray-800/60`}
    >
      <span
        className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${style.icon}`}
      >
        {style.symbol}
      </span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs font-semibold uppercase tracking-wide ${style.label}`}>
            {alert.severity}
          </span>
          <span className="text-slate-400 dark:text-gray-500 text-xs">·</span>
          <span className="text-slate-700 dark:text-gray-300 text-xs font-medium">
            {displayName}
          </span>
          {victimName && victimId && (
            <>
              <span className="text-slate-400 dark:text-gray-500 text-xs">·</span>
              <span className="text-slate-500 dark:text-gray-500 text-xs font-mono">
                {victimId}
              </span>
            </>
          )}
          <span className="text-slate-400 dark:text-gray-500 text-xs">·</span>
          <span className={`text-xs px-1.5 py-0.5 rounded ${style.badge}`}>
            {alert.alert_type?.replace(/_/g, ' ')}
          </span>
          <span className="ml-auto text-slate-400 dark:text-gray-500 text-xs tabular-nums flex-shrink-0">
            {formatTime(alert.timestamp)}
          </span>
        </div>
        <p className="mt-1 text-slate-700 dark:text-gray-300 text-sm leading-snug">
          {alert.message}
        </p>
      </div>
    </div>
  )
}
