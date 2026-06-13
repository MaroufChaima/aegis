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
import { getPriorityVital } from '../../utils/priorityVital'
import { isVictimStatus, getDisplayLabel } from '../../utils/userLabel'

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
      <div className="p-4 text-slate-500 dark:text-gray-400 text-sm">No user selected.</div>
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
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-slate-200 dark:border-gray-700 p-4 space-y-4 max-h-[85vh] overflow-y-auto shadow-sm">

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
            <span className="font-semibold text-slate-900 dark:text-white truncate">
              {victim.name || victim.victim_id}
            </span>
            {displayCategory && (
              <span
                className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium border ${profileColors.bg} ${profileColors.text} ${profileColors.border}`}
              >
                {displayCategory}
              </span>
            )}
            {isVictimStatus(victim) ? (
              <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white">
                Victim
              </span>
            ) : (
              <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-slate-200 dark:bg-gray-700 text-slate-700 dark:text-gray-300">
                User
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-gray-400 font-mono">{victim.victim_id}</p>
          {(victim.age != null || victim.gender) && (
            <p className="text-xs text-slate-500 dark:text-gray-400">
              {[victim.age != null ? `${victim.age} yrs` : null, victim.gender].filter(Boolean).join(' · ')}
            </p>
          )}
          <p className="text-xs text-slate-500 dark:text-gray-400">
            {getPriorityVital(victim).label}: <span className="font-semibold text-slate-800 dark:text-gray-200">{getPriorityVital(victim).formatted}</span>
          </p>
          {(victim.gps_lat != null) && (
            <p className="text-xs text-slate-500 dark:text-gray-400 font-mono">
              {victim.gps_lat.toFixed(4)}, {victim.gps_lon?.toFixed(4)}
              {victim.altitude_m != null ? ` · ${victim.altitude_m.toFixed(0)} m` : ''}
            </p>
          )}
          {conditions.length > 0 && (
            <p className="text-xs text-amber-700 dark:text-amber-300/90">
              Conditions: {conditions.join(', ')}
            </p>
          )}
          <p className="text-xs text-slate-500 dark:text-gray-500">
            Severity {victim.severity_score ?? 0} · Last seen {formatTime(victim.last_seen)}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            type="button"
            onClick={() => setShowHistory(true)}
            className="text-xs px-2 py-1 rounded border border-slate-300 text-slate-600 hover:bg-slate-50 dark:border-gray-600 dark:text-gray-300 dark:hover:text-white dark:hover:border-gray-500 transition-colors"
            aria-label="View vital history"
          >
            History
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="text-slate-500 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white text-sm leading-none"
              aria-label="Close panel"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Alerts — first actionable section */}
      <section>
        <h3 className="text-sm font-semibold text-slate-800 dark:text-gray-200 mb-2 flex items-center gap-2">
          Alerts
          {victimAlerts.length > 0 && (
            <span className="text-xs bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300 px-1.5 py-0.5 rounded-full">
              {victimAlerts.length}
            </span>
          )}
        </h3>
        <div className="rounded-lg overflow-hidden border border-slate-200 dark:border-gray-700 divide-y divide-slate-200 dark:divide-gray-700/60">
          {victimAlerts.length === 0 ? (
            <p className="px-3 py-4 text-center text-slate-500 dark:text-gray-500 text-xs">
              No alerts for this user
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
          <h3 className="text-sm font-semibold text-slate-800 dark:text-gray-200">Vital Signs</h3>
          {victimProfile && (
            <button
              type="button"
              onClick={() => setShowProfileRanges(true)}
              className={`text-xs px-2 py-1 rounded border transition-colors ${
                hasPersonalProfile
                  ? 'border-blue-400 text-blue-700 hover:bg-blue-50 dark:border-blue-500/60 dark:text-blue-300 dark:hover:bg-blue-900/30'
                  : 'border-slate-300 text-slate-500 hover:bg-slate-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700/50'
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
            className="w-full text-left text-xs text-blue-800 bg-blue-50 border border-blue-200 rounded px-2 py-1.5 mb-2 hover:bg-blue-100 dark:text-blue-200/90 dark:bg-blue-900/25 dark:border-blue-600/40 dark:hover:bg-blue-900/40 transition-colors"
          >
            This user has a <span className="font-medium">{displayCategory}</span> profile.
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
                className="bg-slate-50 dark:bg-gray-700/60 rounded p-3 border border-slate-100 dark:border-transparent"
              >
                <p className="text-xs text-slate-500 dark:text-gray-400 mb-0.5">{def.label}</p>
                <p className={`text-lg font-semibold ${
                  outOfRange ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-white'
                }`}>
                  {value != null ? def.format(value) : '—'}
                  <span className="text-xs font-normal text-slate-500 dark:text-gray-400 ml-1">{def.unit}</span>
                </p>
                {rangeHint && (
                  <p className="text-[10px] text-slate-400 dark:text-gray-500 mt-0.5">{rangeHint}</p>
                )}
              </div>
            )
          })}
          {/* GPS position */}
          <div className="bg-slate-50 dark:bg-gray-700/60 rounded p-3 col-span-2 border border-slate-100 dark:border-transparent">
            <p className="text-xs text-slate-500 dark:text-gray-400 mb-0.5">Position (GPS)</p>
            <p className="text-sm font-semibold text-slate-900 dark:text-white">
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
