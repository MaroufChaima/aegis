import React from 'react'
import {
  normalizeWearables,
  resolveWearableStatus,
  resolveWearableBattery,
} from '../../utils/wearableSensors'

function getStatusDotColor(status) {
  switch (status) {
    case 'active':           return 'bg-green-500'
    case 'disconnected':     return 'bg-yellow-500'
    case 'damaged':          return 'bg-red-500'
    case 'battery_depleted': return 'bg-red-500'
    case 'degraded':         return 'bg-orange-500'
    default:                 return 'bg-gray-500'
  }
}

function getStatusLabel(status) {
  switch (status) {
    case 'active':           return 'Active'
    case 'disconnected':     return 'Disconnected'
    case 'damaged':          return 'Damaged'
    case 'battery_depleted': return 'Battery depleted'
    case 'degraded':         return 'Degraded'
    default:                 return 'Unknown'
  }
}

/**
 * WBAN wearable infrastructure — physical sensors only.
 * Shows per-device status and battery; coordinator link info in summary row.
 */
export default function SensorStatusPanel({ assignedSensors = [], victim }) {
  const wearables = normalizeWearables(assignedSensors)
  const sensorStatuses = victim?.sensor_statuses || {}
  const sensorBatteries = victim?.sensor_batteries || {}

  const activeCount = wearables.filter(
    (w) => resolveWearableStatus(w.id, victim, sensorStatuses) === 'active'
      || resolveWearableStatus(w.id, victim, sensorStatuses) === 'degraded',
  ).length

  if (wearables.length === 0 && !victim) {
    return <div className="text-xs text-gray-400">No wearable data available</div>
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Wearable Sensors</h3>
        {wearables.length > 0 && (
          <span className="text-xs text-gray-400">
            {activeCount}/{wearables.length} active
          </span>
        )}
      </div>

      {/* Coordinator link — not a wearable */}
      <div className="grid grid-cols-2 gap-2 p-2 bg-gray-700/30 rounded border border-gray-600/50">
        <div>
          <p className="text-xs text-gray-500">Coordinator link RSSI</p>
          <p className="text-sm font-semibold text-white">
            {victim?.rssi != null ? `${victim.rssi.toFixed(1)} dBm` : '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">UAV relay</p>
          <p className="text-sm font-semibold text-white font-mono">
            {victim?.uav_relay_id || '—'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Packet quality</p>
          <p className="text-sm font-semibold text-white capitalize">
            {victim?.last_packet_quality
              || (victim?.packet_completeness != null
                ? `${(victim.packet_completeness * 100).toFixed(0)}% complete`
                : '—')}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Coordinator battery</p>
          <p className={`text-sm font-semibold ${
            victim?.battery != null && victim.battery < 20 ? 'text-red-400' : 'text-white'
          }`}>
            {victim?.battery != null ? `${victim.battery.toFixed(0)}%` : '—'}
          </p>
        </div>
      </div>

      {wearables.length > 0 ? (
        <div className="rounded border border-gray-600 overflow-hidden">
          <div className="grid grid-cols-3 gap-2 px-2 py-1.5 bg-gray-700/60 text-xs text-gray-400 font-medium">
            <span>Sensor</span>
            <span>Status</span>
            <span className="text-right">Battery</span>
          </div>
          {wearables.map(({ id, label }) => {
            const status = resolveWearableStatus(id, victim, sensorStatuses)
            const battery = resolveWearableBattery(id, sensorBatteries)
            return (
              <div
                key={id}
                className="grid grid-cols-3 gap-2 px-2 py-2 border-t border-gray-700/60 items-center"
              >
                <span className="text-xs text-gray-200">{label}</span>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusDotColor(status)}`} />
                  <span className="text-xs text-gray-400">{getStatusLabel(status)}</span>
                </div>
                <span className={`text-xs text-right font-medium ${
                  battery != null && battery < 20 ? 'text-red-400' : 'text-gray-300'
                }`}>
                  {battery != null ? `${battery.toFixed(0)}%` : '—'}
                </span>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-xs text-gray-500">No sensors assigned to this victim.</p>
      )}
    </div>
  )
}
