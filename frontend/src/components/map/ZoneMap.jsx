import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { MAP_CENTER, DEFAULT_ZOOM } from '../../utils/constants'
import { getPriorityColor } from '../../utils/priorityColors'

/**
 * ZoneMap — Leaflet map showing one CircleMarker per victim.
 *
 * When selectedVictimId is set, that victim gets a larger marker with a white
 * ring so operators can see which dot matches the open detail panel.
 */
export default function ZoneMap({
  victims = [],
  selectedVictimId = null,
  onVictimClick,
}) {
  return (
    <MapContainer
      center={MAP_CENTER}
      zoom={DEFAULT_ZOOM}
      className="w-full h-full rounded-lg"
      style={{ minHeight: '400px' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {victims
        .filter((v) => v.gps_lat != null && v.gps_lon != null)
        .map((victim) => {
          const isSelected = victim.victim_id === selectedVictimId
          const color = getPriorityColor(
            victim.status === 'offline' ? 'offline' : victim.priority_class
          ).hex

          return (
            <CircleMarker
              key={victim.victim_id}
              center={[victim.gps_lat, victim.gps_lon]}
              radius={isSelected ? 16 : 10}
              pathOptions={{
                color: isSelected ? '#ffffff' : color,
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
                <div className="text-sm space-y-1 min-w-[140px]">
                  <p className="font-semibold text-gray-800">
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
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
    </MapContainer>
  )
}
