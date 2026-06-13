import { useState } from 'react'
import ZoneMap from '../components/map/ZoneMap'
import UserQueue from '../components/users/UserQueue'
import VictimDetail from '../components/victims/VictimDetail'
import AlertFeed from '../components/alerts/AlertFeed'
import { useWebSocketContext } from '../contexts/WebSocketContext'
import { REGIONS, REGION_KEYS } from '../utils/regions'
import { pageTitle } from '../utils/themeClasses'

export default function OverviewPage() {
  const { victims, alerts, uavs, region, setRegion } = useWebSocketContext()
  const [selectedUser, setSelectedUser] = useState(null)

  const liveSelected = selectedUser
    ? (victims.find((v) => v.victim_id === selectedUser.victim_id) ?? selectedUser)
    : null

  const handleRegionChange = (key) => {
    setRegion(key)
    setSelectedUser(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className={pageTitle}>Operations Overview</h2>
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-gray-300">
          <span>Region</span>
          <select
            value={region}
            onChange={(e) => handleRegionChange(e.target.value)}
            className="rounded-md border border-slate-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1 text-sm"
          >
            {REGION_KEYS.map((key) => (
              <option key={key} value={key}>{REGIONS[key].label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="h-[480px] rounded-lg overflow-hidden border border-slate-200 dark:border-gray-700 shadow-sm">
        <ZoneMap
          victims={victims}
          uavs={uavs}
          regionKey={region}
          selectedVictimId={liveSelected?.victim_id ?? null}
          onVictimClick={setSelectedUser}
        />
      </div>

      <div className={`flex gap-4 items-start ${liveSelected ? 'flex-col lg:flex-row' : ''}`}>
        <div className={liveSelected ? 'lg:flex-1 w-full' : 'w-full'}>
          <UserQueue
            users={victims}
            selectedId={liveSelected?.victim_id}
            onRowClick={setSelectedUser}
          />
        </div>
        {liveSelected && (
          <div className="lg:w-96 w-full flex-shrink-0">
            <VictimDetail
              victim={liveSelected}
              alerts={alerts}
              onClose={() => setSelectedUser(null)}
            />
          </div>
        )}
      </div>

      <AlertFeed alerts={alerts} victims={victims} />
    </div>
  )
}
