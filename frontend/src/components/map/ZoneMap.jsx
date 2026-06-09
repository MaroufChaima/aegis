import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { MAP_CENTER, DEFAULT_ZOOM } from '../../utils/constants'
import { getPriorityColor } from '../../utils/priorityColors'

/**
 * ZoneMap — Leaflet map showing one CircleMarker per victim.
 *
 * Marker colour is derived from the victim's priority_class via
 * getPriorityColor(). Clicking a marker opens a Popup with the key
 * triage fields the operator needs at a glance.
 *
 * @param {{ victims: Array }} props
 *   victims — array of device objects from GET /api/victims or WebSocket state
 */
export default function ZoneMap({ victims = [] }) {
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
          const color = getPriorityColor(
            victim.status === 'offline' ? 'offline' : victim.priority_class
          ).hex

          return (
            <CircleMarker
              key={victim.victim_id}
              center={[victim.gps_lat, victim.gps_lon]}
              radius={10}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.85,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-sm space-y-1 min-w-[140px]">
                  <p className="font-semibold text-gray-800">{victim.name || victim.victim_id}</p>
                  <p>
                    Priority:{' '}
                    <span style={{ color }} className="font-bold">
                      {victim.priority_class ?? '—'}
                    </span>
                  </p>
                  <p>Heart rate: <span className="font-medium">{victim.heart_rate ?? '—'} bpm</span></p>
                  <p>Temperature: <span className="font-medium">{victim.temperature ?? '—'} °C</span></p>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}
    </MapContainer>
  )
}
