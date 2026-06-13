import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import 'leaflet/dist/leaflet.css'
import { useTheme } from '../../contexts/ThemeContext'
import { getRegion } from '../../utils/regions'
import { getPriorityColor } from '../../utils/priorityColors'
import { REGIONS } from '../../utils/regions'

const TILE_URLS = {
  light: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}

function Recenter({ center, zoom }) {
  const map = useMap()
  useEffect(() => { map.setView(center, zoom) }, [map, center, zoom])
  return null
}

const TEAM_COLOR = '#059669'

export default function RescueTeamMap({ teams = [], users = [], uavs = [], regionKey = 'algiers' }) {
  const { isDark } = useTheme()
  const region = getRegion(regionKey)
  const activeTeams = teams.filter((t) => t.status === 'Active' || t.status === 'deployed')

  return (
    <MapContainer center={region.center} zoom={region.zoom} className="w-full h-full rounded-lg" style={{ minHeight: 320 }}>
      <Recenter center={region.center} zoom={region.zoom} />
      <TileLayer url={isDark ? TILE_URLS.dark : TILE_URLS.light} />

      {activeTeams
        .filter((t) => t.latitude != null && t.longitude != null)
        .map((team) => (
          <CircleMarker
            key={team.team_id}
            center={[team.latitude, team.longitude]}
            radius={12}
            pathOptions={{ color: TEAM_COLOR, fillColor: TEAM_COLOR, fillOpacity: 0.75, weight: 2 }}
          >
            <Popup>
              <div className="text-sm text-slate-800">
                <p className="font-semibold">{team.team_name}</p>
                <p>{team.team_type?.replace(/_/g, ' ')}</p>
                <p>Personnel: {team.personnel_count ?? team.member_count}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

      {uavs
        .filter((u) => u.latitude != null && u.longitude != null)
        .map((uav) => (
          <CircleMarker
            key={uav.uav_id}
            center={[uav.latitude, uav.longitude]}
            radius={8}
            pathOptions={{ color: '#2563eb', fillColor: '#60a5fa', fillOpacity: 0.7, weight: 2 }}
          />
        ))}

      {users
        .filter((u) => u.gps_lat != null && u.gps_lon != null)
        .map((u) => (
          <CircleMarker
            key={u.victim_id}
            center={[u.gps_lat, u.gps_lon]}
            radius={7}
            pathOptions={{
              color: getPriorityColor(u.priority_class ?? 'P3').hex,
              fillColor: getPriorityColor(u.priority_class ?? 'P3').hex,
              fillOpacity: 0.8,
              weight: 2,
            }}
          />
        ))}
    </MapContainer>
  )
}
