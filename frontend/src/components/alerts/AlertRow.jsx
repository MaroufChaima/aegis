/**
 * Severity → visual style mapping.
 * Applied to the left border, icon background, and label text.
 */
const SEVERITY = {
  critical: {
    border: 'border-red-500',
    icon:   'bg-red-500/20 text-red-400',
    label:  'text-red-400',
    badge:  'bg-red-500/20 text-red-300',
    symbol: '⚠',
  },
  warning: {
    border: 'border-amber-400',
    icon:   'bg-amber-400/20 text-amber-300',
    label:  'text-amber-300',
    badge:  'bg-amber-400/20 text-amber-200',
    symbol: '!',
  },
  info: {
    border: 'border-blue-400',
    icon:   'bg-blue-400/20 text-blue-300',
    label:  'text-blue-300',
    badge:  'bg-blue-400/20 text-blue-200',
    symbol: 'i',
  },
}

const DEFAULT_SEVERITY = {
  border: 'border-gray-600',
  icon:   'bg-gray-600/20 text-gray-400',
  label:  'text-gray-400',
  badge:  'bg-gray-600/20 text-gray-300',
  symbol: '•',
}

/**
 * Format an ISO timestamp to HH:MM:SS local time.
 */
function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d) ? '' : d.toLocaleTimeString()
}

/**
 * AlertRow — renders a single alert entry in the feed.
 *
 * @param {{ alert: object }} props
 *   alert.severity   — "critical" | "warning" | "info"
 *   alert.alert_type — snake_case type identifier
 *   alert.device_id  — originating device
 *   alert.message    — human-readable description
 *   alert.timestamp  — ISO 8601 string
 */
export default function AlertRow({ alert }) {
  const style = SEVERITY[alert.severity] ?? DEFAULT_SEVERITY

  return (
    <div className={`flex items-start gap-3 px-4 py-3 border-l-2 ${style.border} bg-gray-800/60`}>
      {/* Severity icon */}
      <span
        className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${style.icon}`}
      >
        {style.symbol}
      </span>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs font-semibold uppercase tracking-wide ${style.label}`}>
            {alert.severity}
          </span>
          <span className="text-gray-500 text-xs">·</span>
          <span className="text-gray-400 text-xs font-mono">{alert.device_id}</span>
          <span className="text-gray-500 text-xs">·</span>
          <span className={`text-xs px-1.5 py-0.5 rounded ${style.badge}`}>
            {alert.alert_type?.replace(/_/g, ' ')}
          </span>
          <span className="ml-auto text-gray-500 text-xs tabular-nums flex-shrink-0">
            {formatTime(alert.timestamp)}
          </span>
        </div>
        <p className="mt-1 text-gray-300 text-sm leading-snug">{alert.message}</p>
      </div>
    </div>
  )
}
