import React from 'react'
import { SENSOR_LABELS, SENSOR_UNITS } from '../../utils/constants'
import ImputationBadge from './ImputationBadge'

function getStatusDotColor(status) {
  switch (status) {
    case 'active':           return 'bg-green-500'
    case 'disconnected':     return 'bg-yellow-500'
    case 'damaged':          return 'bg-red-500'
    case 'battery_depleted': return 'bg-red-500'
    case 'degraded':         return 'bg-orange-500'
    default:                 return 'bg-gray-400'
  }
}

/**
 * Displays a grid of all sensors assigned to a victim showing their current
 * status (active/disconnected/damaged), their current value, and whether the
 * value was directly measured or estimated. Imputed values are marked with a
 * tilde badge showing the confidence percentage.
 **/
export default function SensorStatusPanel({ sensorStatuses, readings }) {
  if (!sensorStatuses && !readings) {
    return <div className="text-xs text-gray-400">No sensor data available</div>
  }

  const GPS_KEYS = new Set(['gps_lat', 'gps_lon'])

  const sensorIds = [
    ...new Set([
      ...Object.keys(sensorStatuses || {}),
      ...Object.keys(readings || {}),
    ]),
  ]
    .filter(id => !GPS_KEYS.has(id))
    .sort()

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Sensor Status</h3>
      <div className="grid grid-cols-2 gap-2">
        {sensorIds.map(id => {
          const reading = readings?.[id]
          const dotColor = getStatusDotColor(sensorStatuses?.[id])
          const label = SENSOR_LABELS[id] || id

          let displayValue = '—'
          if (reading) {
            if (reading.raw_value != null) {
              displayValue = reading.raw_value.toFixed(1)
            } else if (reading.imputed_value != null) {
              displayValue = reading.imputed_value.toFixed(1)
            }
          }

          return (
            <div
              key={id}
              className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-200"
            >
              <div className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${dotColor}`} />
                <span className="text-xs text-gray-700">{label}</span>
              </div>
              <div className="flex items-center gap-0.5">
                {reading ? (
                  <>
                    <span className="text-xs font-medium text-gray-800">{displayValue}</span>
                    <span className="text-xs text-gray-500 ml-0.5">{SENSOR_UNITS[id] || ''}</span>
                    <ImputationBadge
                      method={reading.imputation_method}
                      confidence={reading.imputation_confidence}
                    />
                  </>
                ) : (
                  <span className="text-xs text-gray-400">no data</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
