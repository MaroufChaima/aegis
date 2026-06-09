import { useState, useEffect } from 'react'
import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'
import SensorStatusPanel from './SensorStatusPanel'
import { fetchVictimProfile } from '../../api/profiles'

/**
 * Format an ISO timestamp to a short HH:MM:SS local string.
 * Returns '—' if the value is null/undefined.
 */
function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

/**
 * VictimDetail — expanded view for a single victim.
 *
 * Displays priority, current vitals, WBAN sensor status grid, and the
 * physiological profile fetched from the API. Intended to be rendered
 * inside a side panel or modal when the operator selects a row or marker.
 *
 * @param {{ victim: object, onClose: function }} props
 *   victim  — device object from WebSocket state / GET /api/victims
 *   onClose — optional callback to close the panel
 */
export default function VictimDetail({ victim, onClose }) {
  const [victimProfile, setVictimProfile] = useState(null)
  const [sensorReadings, setSensorReadings] = useState(null)

  useEffect(() => {
    if (!victim) return
    const victimId = victim.victim_id || victim.device_id
    if (!victimId) return
    fetchVictimProfile(victimId)
      .then(profile => setVictimProfile(profile))
      .catch(err => console.warn('Could not load victim profile:', err))
  }, [victim?.victim_id, victim?.device_id])

  if (!victim) {
    return (
      <div className="p-4 text-gray-400 text-sm">No victim selected.</div>
    )
  }

  const priority = victim.status === 'offline' ? 'offline' : (victim.priority_class ?? 'P3')
  const color = getPriorityColor(priority)

  // Use the enriched victim field first; fall back to the fetched profile once loaded.
  const displayCategory = victim.risk_category || victimProfile?.risk_category
  const profileColors = PROFILE_COLORS[displayCategory] || PROFILE_COLORS.unknown

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 space-y-4">

      {/* Header — device ID, priority badge, optional close button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
            style={{ backgroundColor: color.hex }}
          >
            {priority}
          </span>
          <span className="font-mono font-semibold text-white">{victim.device_id}</span>
          {displayCategory && (
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium border ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}
            >
              {displayCategory}
            </span>
          )}
          {victim.sos_signal && (
            <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white animate-pulse">
              SOS
            </span>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-sm leading-none"
            aria-label="Close panel"
          >
            ✕
          </button>
        )}
      </div>

      {/* Vitals summary cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-700/60 rounded p-3">
          <p className="text-xs text-gray-400 mb-0.5">Heart Rate</p>
          <p className={`text-lg font-semibold ${
            victim.heart_rate != null && (victim.heart_rate < 50 || victim.heart_rate > 120)
              ? 'text-red-400'
              : 'text-white'
          }`}>
            {victim.heart_rate != null ? `${victim.heart_rate}` : '—'}
            <span className="text-xs font-normal text-gray-400 ml-1">bpm</span>
          </p>
        </div>

        <div className="bg-gray-700/60 rounded p-3">
          <p className="text-xs text-gray-400 mb-0.5">Temperature</p>
          <p className={`text-lg font-semibold ${
            victim.temperature != null && victim.temperature > 38.5
              ? 'text-red-400'
              : 'text-white'
          }`}>
            {victim.temperature != null ? `${victim.temperature}` : '—'}
            <span className="text-xs font-normal text-gray-400 ml-1">°C</span>
          </p>
        </div>

        <div className="bg-gray-700/60 rounded p-3">
          <p className="text-xs text-gray-400 mb-0.5">Severity</p>
          <p className="text-lg font-semibold text-white">
            {victim.severity_score ?? '—'}
          </p>
        </div>
      </div>

      {/* Last seen */}
      <p className="text-xs text-gray-400">
        Last seen: <span className="text-gray-300">{formatTime(victim.last_seen)}</span>
      </p>

      {/* WBAN Sensor Status — added in migration M6 */}
      <div className="mt-4">
        <SensorStatusPanel
          sensorStatuses={victim?.sensor_statuses || null}
          readings={sensorReadings}
        />
      </div>

      {victimProfile && (
        <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
          <h3 className="text-sm font-semibold text-blue-800 mb-2">Physiological Profile</h3>
          <div className="grid grid-cols-2 gap-1 text-xs text-blue-700">
            <span>Profile type:</span><span className="font-medium">{victimProfile.risk_category || 'unknown'}</span>
            <span>HR normal range:</span><span className="font-medium">{victimProfile.hr_normal_min}–{victimProfile.hr_normal_max} bpm</span>
            <span>Temp normal range:</span><span className="font-medium">{victimProfile.temp_normal_min}–{victimProfile.temp_normal_max} °C</span>
            {victimProfile.glucose_normal_min && <><span>Glucose range:</span><span className="font-medium">{victimProfile.glucose_normal_min}–{victimProfile.glucose_normal_max} mg/dL</span></>}
          </div>
        </div>
      )}

    </div>
  )
}
