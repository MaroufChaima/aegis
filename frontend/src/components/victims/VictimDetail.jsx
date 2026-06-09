import { useState, useEffect, useMemo } from 'react'
import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'
import {
  VITAL_DEFS,
  getOrderedVitalKeys,
  getPriorityVitalKeys,
  getAwarenessNote,
} from '../../utils/vitalPriority'
import SensorStatusPanel from './SensorStatusPanel'
import AlertRow from '../alerts/AlertRow'
import { fetchVictimProfile } from '../../api/profiles'

function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleTimeString()
}

function parseConditions(medicalConditions) {
  if (!medicalConditions) return []
  try {
    const parsed = JSON.parse(medicalConditions)
    return Array.isArray(parsed) ? parsed : [medicalConditions]
  } catch {
    return medicalConditions ? [medicalConditions] : []
  }
}

/**
 * VictimDetail — side panel with alerts, vitals, and wearable network status.
 */
export default function VictimDetail({ victim, alerts = [], onClose }) {
  const [victimProfile, setVictimProfile] = useState(null)

  useEffect(() => {
    if (!victim) return
    const victimId = victim.victim_id || victim.device_id
    if (!victimId) return
    fetchVictimProfile(victimId)
      .then((profile) => setVictimProfile(profile))
      .catch((err) => console.warn('Could not load victim profile:', err))
  }, [victim?.victim_id, victim?.device_id])

  const victimAlerts = useMemo(() => {
    if (!victim) return []
    const id = victim.victim_id || victim.device_id
    return alerts.filter((a) => a.victim_id === id || a.device_id === id)
  }, [alerts, victim])

  if (!victim) {
    return (
      <div className="p-4 text-gray-400 text-sm">No victim selected.</div>
    )
  }

  const priority = victim.status === 'offline' ? 'offline' : (victim.priority_class ?? 'P3')
  const color = getPriorityColor(priority)
  const displayCategory = victim.risk_category || victimProfile?.risk_category
  const profileColors = PROFILE_COLORS[displayCategory] || PROFILE_COLORS.unknown
  const awarenessNote = getAwarenessNote(displayCategory)
  const assignedSensors = victimProfile?.assigned_sensors || []
  const orderedVitalKeys = getOrderedVitalKeys(displayCategory, assignedSensors)
  const priorityVitalKeys = getPriorityVitalKeys(displayCategory, assignedSensors)
  const conditions = parseConditions(victim.medical_conditions)

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 space-y-4 max-h-[85vh] overflow-y-auto">

      {/* Victim information card */}
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1.5 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="inline-block px-2 py-0.5 rounded text-xs font-bold text-white"
              style={{ backgroundColor: color.hex }}
            >
              {priority}
            </span>
            <span className="font-semibold text-white truncate">
              {victim.name || victim.victim_id}
            </span>
            {displayCategory && (
              <span
                className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium border ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}
              >
                {displayCategory}
              </span>
            )}
            {victim.sos_active ? (
              <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white animate-pulse">
                SOS
              </span>
            ) : null}
          </div>
          <p className="text-xs text-gray-400 font-mono">{victim.victim_id}</p>
          {(victim.age != null || victim.gender) && (
            <p className="text-xs text-gray-400">
              {[victim.age != null ? `${victim.age} yrs` : null, victim.gender].filter(Boolean).join(' · ')}
            </p>
          )}
          {conditions.length > 0 && (
            <p className="text-xs text-amber-300/90">
              Conditions: {conditions.join(', ')}
            </p>
          )}
          <p className="text-xs text-gray-500">
            Severity {victim.severity_score ?? 0} · Last seen {formatTime(victim.last_seen)}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-sm leading-none flex-shrink-0"
            aria-label="Close panel"
          >
            ✕
          </button>
        )}
      </div>

      {/* Alerts — first actionable section */}
      <section>
        <h3 className="text-sm font-semibold text-gray-200 mb-2 flex items-center gap-2">
          Alerts
          {victimAlerts.length > 0 && (
            <span className="text-xs bg-red-900/50 text-red-300 px-1.5 py-0.5 rounded-full">
              {victimAlerts.length}
            </span>
          )}
        </h3>
        <div className="rounded-lg overflow-hidden border border-gray-700 divide-y divide-gray-700/60">
          {victimAlerts.length === 0 ? (
            <p className="px-3 py-4 text-center text-gray-500 text-xs">
              No alerts for this victim
            </p>
          ) : (
            victimAlerts.slice(0, 8).map((alert, i) => (
              <AlertRow key={alert.id ?? `${alert.timestamp}-${i}`} alert={alert} />
            ))
          )}
        </div>
      </section>

      {/* Vital signs — physiological only */}
      <section>
        <h3 className="text-sm font-semibold text-gray-200 mb-2">Vital Signs</h3>
        {awarenessNote && (
          <p className="text-xs text-amber-200/90 bg-amber-900/30 border border-amber-700/50 rounded px-2 py-1.5 mb-2">
            {awarenessNote}
          </p>
        )}
        <div className="grid grid-cols-2 gap-2">
          {orderedVitalKeys.map((key) => {
            const def = VITAL_DEFS[key]
            const value = victim[key]
            const isPriority = priorityVitalKeys.includes(key)
            return (
              <div
                key={key}
                className={`bg-gray-700/60 rounded p-3 border ${
                  isPriority && displayCategory && displayCategory !== 'healthy'
                    ? 'border-amber-600/40'
                    : 'border-transparent'
                }`}
              >
                <p className="text-xs text-gray-400 mb-0.5">
                  {def.label}
                  {isPriority && displayCategory && displayCategory !== 'healthy' && (
                    <span className="ml-1 text-amber-400" title="Priority vital for this profile">★</span>
                  )}
                </p>
                <p className={`text-lg font-semibold ${
                  value != null && def.isAlert(value) ? 'text-red-400' : 'text-white'
                }`}>
                  {value != null ? def.format(value) : '—'}
                  <span className="text-xs font-normal text-gray-400 ml-1">{def.unit}</span>
                </p>
              </div>
            )
          })}
          {/* GPS position */}
          <div className="bg-gray-700/60 rounded p-3 col-span-2">
            <p className="text-xs text-gray-400 mb-0.5">Position (GPS)</p>
            <p className="text-sm font-semibold text-white">
              {victim.gps_lat != null
                ? `${victim.gps_lat.toFixed(4)}, ${victim.gps_lon.toFixed(4)}`
                : '—'}
            </p>
          </div>
        </div>
      </section>

      {/* Wearable network — infrastructure, not vitals */}
      <section>
        <SensorStatusPanel
          assignedSensors={assignedSensors}
          victim={victim}
        />
      </section>

      {victimProfile && (
        <section className="p-3 bg-gray-700/40 rounded border border-gray-600">
          <h3 className="text-sm font-semibold text-gray-200 mb-2">Physiological Profile</h3>
          <div className="grid grid-cols-2 gap-1 text-xs text-gray-300">
            <span>HR normal:</span>
            <span className="font-medium">{victimProfile.hr_normal_min}–{victimProfile.hr_normal_max} bpm</span>
            <span>Temp normal:</span>
            <span className="font-medium">{victimProfile.temp_normal_min}–{victimProfile.temp_normal_max} °C</span>
            {victimProfile.glucose_normal_min && (
              <>
                <span>Glucose range:</span>
                <span className="font-medium">{victimProfile.glucose_normal_min}–{victimProfile.glucose_normal_max} mg/dL</span>
              </>
            )}
          </div>
        </section>
      )}
    </div>
  )
}
