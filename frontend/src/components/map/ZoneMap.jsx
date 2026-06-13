import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import 'leaflet/dist/leaflet.css'
import { getPriorityColor } from '../../utils/priorityColors'
import { useTheme } from '../../contexts/ThemeContext'
import { getRegion } from '../../utils/regions'

const TILE_URLS = {
  light: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
}

function MapRecenter({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom)
  }, [map, center, zoom])
  return null
}

export default function ZoneMap({
  victims = [],
  uavs = [],
  regionKey = 'algiers',
  selectedVictimId = null,
  onVictimClick,
}) {
  const { isDark } = useTheme()
  const tileUrl = isDark ? TILE_URLS.dark : TILE_URLS.light
  const region = getRegion(regionKey)

  return (
    <MapContainer
      center={region.center}
      zoom={region.zoom}
      className="w-full h-full rounded-lg"
      style={{ minHeight: '400px' }}
    >
      <MapRecenter center={region.center} zoom={region.zoom} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url={tileUrl}
      />

      {uavs
        .filter((u) => u.latitude != null && u.longitude != null)
        .map((uav) => (
          <CircleMarker
            key={uav.uav_id}
            center={[uav.latitude, uav.longitude]}
            radius={12}
            pathOptions={{
              color: isDark ? '#60a5fa' : '#2563eb',
              fillColor: uav.status === 'offline' ? '#94a3b8' : '#3b82f6',
              fillOpacity: 0.7,
              weight: 2,
              dashArray: uav.status === 'offline' ? '4 4' : undefined,
            }}
          >
            <Popup>
              <div className="text-sm space-y-1 min-w-[160px] text-slate-800">
                <p className="font-semibold">{uav.name || uav.uav_id}</p>
                <p>Status: <span className="font-medium">{uav.status}</span></p>
                <p>Battery: <span className="font-medium">{uav.battery ?? '—'}%</span></p>
                <p>Devices: <span className="font-medium">{uav.connected_devices ?? 0}</span></p>
              </div>
            </Popup>
          </CircleMarker>
        ))}

      {victims
        .filter((v) => v.gps_lat != null && v.gps_lon != null)
        .map((victim) => {
          const isSelected = victim.victim_id === selectedVictimId
          const color = getPriorityColor(
            victim.status === 'offline' ? 'offline' : victim.priority_class
          ).hex
          const ringColor = isDark ? '#ffffff' : '#1e293b'

          return (
            <CircleMarker
              key={victim.victim_id}
              center={[victim.gps_lat, victim.gps_lon]}
              radius={isSelected ? 16 : 10}
              pathOptions={{
                color: isSelected ? ringColor : color,
                fillColor: color,
                fillOpacity: isSelected ? 1 : 0.85,
                weight: isSelected ? 4 : 2,
              }}
              eventHandlers={
                onVictimClick
                  ? { click: () => onVictimClick(victim) }
                  : undefined
              }
            >
              <Popup>
                <div className="text-sm space-y-1 min-w-[140px] text-slate-800">
                  <p className="font-semibold">
                    {victim.name || victim.victim_id}
                    {isSelected ? (
                      <span className="ml-1 text-xs text-blue-600 font-medium">
                        (selected)
                      </span>
                    ) : null}
                  </p>
                  <p>
                    Priority:{' '}
                    <span style={{ color }} className="font-bold">
                      {victim.priority_class ?? '—'}
                    </span>
                  </p>
                  <p>
                    Heart rate:{' '}
                    <span className="font-medium">{victim.heart_rate ?? '—'} bpm</span>
                  </p>
                  <p>
                    Temperature:{' '}
                    <span className="font-medium">{victim.temperature ?? '—'} °C</span>
                  </p>
                  {victim.altitude_m != null && (
                    <p>
                      Altitude:{' '}
                      <span className="font-medium">{victim.altitude_m.toFixed(0)} m</span>
                    </p>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
    </MapContainer>
  )
}
