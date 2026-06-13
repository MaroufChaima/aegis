import { MapContainer, TileLayer, CircleMarker, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import 'leaflet/dist/leaflet.css'
import { getPriorityColor } from '../../utils/priorityColors'
import { useTheme } from '../../contexts/ThemeContext'

const TILE_URLS = {
  light: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}

function Recenter({ center, zoom }) {
  const map = useMap()
  useEffect(() => { map.setView(center, zoom) }, [map, center, zoom])
  return null
}

export default function UAVMiniMap({ uav, users = [], height = 180 }) {
  const { isDark } = useTheme()
  if (uav?.latitude == null || uav?.longitude == null) {
    return (
      <div className="rounded bg-slate-100 dark:bg-gray-900 flex items-center justify-center text-xs text-slate-500" style={{ height }}>
        No position
      </div>
    )
  }

  const center = [uav.latitude, uav.longitude]
  const connected = users.length ? users : (uav.connected_users ?? uav.connected_victims ?? [])

  return (
    <div className="rounded overflow-hidden border border-slate-200 dark:border-gray-700" style={{ height }}>
      <MapContainer center={center} zoom={15} className="w-full h-full" zoomControl={false} attributionControl={false} dragging={false} scrollWheelZoom={false}>
        <Recenter center={center} zoom={15} />
        <TileLayer url={isDark ? TILE_URLS.dark : TILE_URLS.light} />
        <CircleMarker
          center={center}
          radius={10}
          pathOptions={{ color: '#2563eb', fillColor: '#3b82f6', fillOpacity: 0.9, weight: 2 }}
        />
        {connected
          .filter((u) => u.gps_lat != null && u.gps_lon != null)
          .map((u) => (
            <CircleMarker
              key={u.victim_id}
              center={[u.gps_lat, u.gps_lon]}
              radius={7}
              pathOptions={{
                color: getPriorityColor(u.priority_class ?? 'P3').hex,
                fillColor: getPriorityColor(u.priority_class ?? 'P3').hex,
                fillOpacity: 0.85,
                weight: 2,
              }}
            />
          ))}
      </MapContainer>
    </div>
  )
}
