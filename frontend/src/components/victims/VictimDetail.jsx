import { useState, useEffect, useMemo } from 'react'
import { getPriorityColor } from '../../utils/priorityColors'
import { PROFILE_COLORS } from '../../utils/constants'
import {
  VITAL_DEFS,
  getOrderedVitalKeys,
} from '../../utils/vitalPriority'
import {
  isOutsidePersonalRange,
  getPersonalRangeHint,
} from '../../utils/personalThresholds'
import SensorStatusPanel from './SensorStatusPanel'
import AlertRow from '../alerts/AlertRow'
import ProfileRangesModal from './ProfileRangesModal'
import VictimHistoryModal from './VictimHistoryModal'
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
  const [showProfileRanges, setShowProfileRanges] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState([])

  useEffect(() => {
    setHistory([])
    setShowHistory(false)
  }, [victim?.victim_id])

  useEffect(() => {
    if (!victim?.victim_id || !victim?.last_seen) return
    const snap = {
      timestamp: victim.last_seen,
      heart_rate: victim.heart_rate,
      temperature: victim.temperature,
      spo2: victim.spo2,
      respiratory_rate: victim.respiratory_rate,
      severity_score: victim.severity_score,
      priority_class: victim.priority_class,
    }
    setHistory((prev) => {
      if (prev[0]?.timestamp === snap.timestamp) return prev
      return [snap, ...prev].slice(0, 50)
    })
  }, [
    victim?.victim_id,
    victim?.last_seen,
    victim?.heart_rate,
    victim?.temperature,
    victim?.spo2,
    victim?.respiratory_rate,
    victim?.severity_score,
    victim?.priority_class,
  ])

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
  const assignedSensors = victimProfile?.assigned_sensors || []
  const orderedVitalKeys = getOrderedVitalKeys(displayCategory, assignedSensors)
  const conditions = parseConditions(victim.medical_conditions)
  const hasPersonalProfile = victimProfile && displayCategory && displayCategory !== 'healthy'

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
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            type="button"
            onClick={() => setShowHistory(true)}
            className="text-xs px-2 py-1 rounded border border-gray-600 text-gray-300 hover:text-white hover:border-gray-500"
            aria-label="View vital history"
          >
            History
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-white text-sm leading-none"
              aria-label="Close panel"
            >
              ✕
            </button>
          )}
        </div>
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
              <AlertRow
                key={alert.id ?? `${alert.timestamp}-${i}`}
                alert={alert}
                victimName={victim.name || victim.victim_id}
              />
            ))
          )}
        </div>
      </section>

      {/* Vital signs — physiological only */}
      <section>
        <div className="flex items-center justify-between gap-2 mb-2">
          <h3 className="text-sm font-semibold text-gray-200">Vital Signs</h3>
          {victimProfile && (
            <button
              type="button"
              onClick={() => setShowProfileRanges(true)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${
                hasPersonalProfile
                  ? 'border-blue-500/60 text-blue-300 hover:bg-blue-900/30'
                  : 'border-gray-600 text-gray-400 hover:bg-gray-700/50'
              }`}
            >
              View normal ranges
            </button>
          )}
        </div>
        {hasPersonalProfile && (
          <button
            type="button"
            onClick={() => setShowProfileRanges(true)}
            className="w-full text-left text-xs text-blue-200/90 bg-blue-900/25 border border-blue-600/40 rounded px-2 py-1.5 mb-2 hover:bg-blue-900/40 transition-colors"
          >
            This victim has a <span className="font-medium">{displayCategory}</span> profile.
            Tap to see their personalized normal ranges before interpreting vitals.
          </button>
        )}
        <div className="grid grid-cols-2 gap-2">
          {orderedVitalKeys.map((key) => {
            const def = VITAL_DEFS[key]
            const value = victim[key]
            const outOfRange = value != null && isOutsidePersonalRange(
              key, value, victimProfile, def.isAlert,
            )
            const rangeHint = getPersonalRangeHint(key, victimProfile)
            return (
              <div
                key={key}
                className="bg-gray-700/60 rounded p-3 border border-transparent"
              >
                <p className="text-xs text-gray-400 mb-0.5">{def.label}</p>
                <p className={`text-lg font-semibold ${
                  outOfRange ? 'text-red-400' : 'text-white'
                }`}>
                  {value != null ? def.format(value) : '—'}
                  <span className="text-xs font-normal text-gray-400 ml-1">{def.unit}</span>
                </p>
                {rangeHint && (
                  <p className="text-[10px] text-gray-500 mt-0.5">{rangeHint}</p>
                )}
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

      {showProfileRanges && victimProfile && (
        <ProfileRangesModal
          profile={victimProfile}
          onClose={() => setShowProfileRanges(false)}
        />
      )}

      {showHistory && (
        <VictimHistoryModal
          victim={victim}
          history={history}
          onClose={() => setShowHistory(false)}
        />
      )}
    </div>
  )
}
