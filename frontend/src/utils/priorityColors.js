// Single source of truth for priority → colour mappings.
// Used by VictimMarker (Leaflet), VictimRow (table highlight),
// and PriorityPie (chart segment colours).

export const PRIORITY_COLORS = {
  P1: {
    bg: 'bg-red-600',
    text: 'text-red-600',
    hex: '#dc2626',
    label: 'Critical',
  },
  P2: {
    bg: 'bg-orange-500',
    text: 'text-orange-500',
    hex: '#f97316',
    label: 'Urgent',
  },
  P3: {
    bg: 'bg-green-500',
    text: 'text-green-500',
    hex: '#22c55e',
    label: 'Stable',
  },
  offline: {
    bg: 'bg-gray-400',
    text: 'text-gray-400',
    hex: '#9ca3af',
    label: 'Offline',
  },
}

/**
 * Returns the colour config for a given priority class or device status.
 * Falls back to the offline palette for any unrecognised value.
 *
 * @param {string} priority - "P1" | "P2" | "P3" | "offline"
 * @returns {{ bg: string, text: string, hex: string, label: string }}
 */
export function getPriorityColor(priority) {
  return PRIORITY_COLORS[priority] ?? PRIORITY_COLORS.offline
}
