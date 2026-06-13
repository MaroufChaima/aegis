import { useEffect, useState } from 'react'
import { fetchRescueTeam, fetchRescuer } from '../api/rescueTeams'
import { useWebSocketContext } from '../contexts/WebSocketContext'
import RescueTeamMap from '../components/map/RescueTeamMap'
import { card, errorBanner, muted, pageTitle } from '../utils/themeClasses'
import { REGIONS, REGION_KEYS } from '../utils/regions'

const STATUS_COLORS = {
  Active: 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400',
  Standby: 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400',
  'Out of Service': 'bg-slate-100 text-slate-600 dark:bg-gray-500/20 dark:text-gray-400',
  deployed: 'bg-green-100 text-green-700',
  standby: 'bg-amber-100 text-amber-700',
}

function TeamList({ teams, onSelect }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {teams.map((team) => (
        <button
          key={team.team_id}
          type="button"
          onClick={() => onSelect(team.team_id)}
          className={`${card} p-4 text-left hover:shadow-md w-full`}
        >
          <div className="flex justify-between gap-2 mb-2">
            <div>
              <p className="font-semibold text-slate-900 dark:text-white">{team.team_name}</p>
              <p className="text-xs text-slate-500 font-mono">{team.team_id}</p>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[team.status] ?? ''}`}>
              {team.status}
            </span>
          </div>
          <p className="text-sm capitalize text-slate-600 dark:text-gray-300">
            {(team.team_type || team.specialization)?.replace(/_/g, ' ')} · {REGIONS[team.current_region]?.label}
          </p>
          <p className={`text-xs ${muted} mt-2`}>
            {team.personnel_count ?? team.member_count} personnel · {team.assigned_victim_count ?? 0} users · {(team.assigned_uavs ?? []).length} UAVs
          </p>
        </button>
      ))}
    </div>
  )
}

export default function RescueTeamsPage() {
  const { teams, victims, uavs, region, setRegion } = useWebSocketContext()
  const [team, setTeam] = useState(null)
  const [rescuer, setRescuer] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => { setTeam(null); setRescuer(null) }, [region])

  const openTeam = async (teamId) => {
    try {
      setTeam(await fetchRescueTeam(teamId))
      setRescuer(null)
    } catch (e) { setError(e.message) }
  }

  const openRescuer = async (rescuerId) => {
    try { setRescuer(await fetchRescuer(rescuerId)) } catch (e) { setError(e.message) }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className={pageTitle}>Rescue Teams</h2>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="rounded border border-slate-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
        >
          {REGION_KEYS.map((k) => (
            <option key={k} value={k}>{REGIONS[k].label}</option>
          ))}
        </select>
      </div>

      {error && <div className={errorBanner}>{error}</div>}

      <div className="h-80 rounded-lg overflow-hidden border border-slate-200 dark:border-gray-700">
        <RescueTeamMap teams={teams} users={victims} uavs={uavs} regionKey={region} />
      </div>

      {!team && !rescuer && (
        teams.length === 0 ? (
          <p className={`${muted} text-center py-12`}>No rescue teams in this region.</p>
        ) : (
          <TeamList teams={teams} onSelect={openTeam} />
        )
      )}

      {team && !rescuer && (
        <div className="space-y-4">
          <button type="button" onClick={() => setTeam(null)} className="text-sm text-blue-600 hover:underline">← All teams</button>
          <div className={`${card} p-4`}>
            <h3 className="font-semibold text-lg">{team.team_name}</h3>
            <p className={`text-sm ${muted}`}>Assigned users: {team.assigned_users?.join(', ') || '—'}</p>
            <p className={`text-sm ${muted}`}>Assigned UAVs: {team.assigned_uavs?.join(', ') || '—'}</p>
            <p className="text-sm">Coordinates: {team.latitude?.toFixed(4)}, {team.longitude?.toFixed(4)}</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {team.members?.map((m) => (
              <button key={m.rescuer_id} type="button" onClick={() => openRescuer(m.rescuer_id)} className={`${card} p-3 text-left`}>
                <p className="font-medium">{m.first_name} {m.last_name}</p>
                <p className="text-xs text-slate-500 capitalize">{m.role}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {rescuer && (
        <div className="space-y-4">
          <button type="button" onClick={() => setRescuer(null)} className="text-sm text-blue-600 hover:underline">← Back</button>
          <div className={`${card} p-4`}>
            <h3 className="font-semibold">{rescuer.first_name} {rescuer.last_name}</h3>
            <p className="text-sm capitalize">{rescuer.role} · {rescuer.years_experience} yrs exp</p>
          </div>
        </div>
      )}
    </div>
  )
}
