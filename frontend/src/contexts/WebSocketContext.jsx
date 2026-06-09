import { useContext, useEffect, useState, createContext } from 'react'
import useWebSocket from '../hooks/useWebSocket'
import { fetchVictims } from '../api/victims'
import { fetchUAVs } from '../api/uavs'
import { WS_URL } from '../utils/constants'

const WebSocketContext = createContext(null)

/** Identity fields from REST — never overwrite with null from WS telemetry payloads. */
const PRESERVE_IF_NULL = [
  'name', 'age', 'gender', 'risk_category', 'medical_conditions',
  'is_athlete', 'pregnancy_status',
]

function mergeVictimUpdate(existing, payload) {
  const merged = { ...existing, ...payload }
  for (const field of PRESERVE_IF_NULL) {
    if ((payload[field] == null || payload[field] === '') && existing[field] != null) {
      merged[field] = existing[field]
    }
  }
  if (payload.sensor_statuses) {
    merged.sensor_statuses = { ...existing.sensor_statuses, ...payload.sensor_statuses }
  }
  if (payload.sensor_batteries) {
    merged.sensor_batteries = { ...existing.sensor_batteries, ...payload.sensor_batteries }
  }
  return merged
}

/**
 * WebSocketProvider — connects to the backend WebSocket and maintains
 * the live state of victims, alerts, and UAVs for the entire dashboard.
 *
 * Message routing:
 *   "telemetry_update" → upserts the device in the victims array
 *   "alert"            → prepends the alert to the alerts array (cap 100)
 *   "uav_update"       → upserts the UAV in the uavs array by uav_id
 *
 * On mount, seeds victims and UAVs from REST so pages populate immediately.
 *
 * @param {{ children: React.ReactNode }} props
 */
export function WebSocketProvider({ children }) {
  const [victims, setVictims] = useState([])
  const [alerts,  setAlerts]  = useState([])
  const [uavs,    setUAVs]    = useState([])

  const { lastMessage, connectionStatus } = useWebSocket(WS_URL)

  // Seed victims and UAVs from REST on first load
  useEffect(() => {
    fetchVictims()
      .then(setVictims)
      .catch((err) => console.error('[WebSocketContext] Victims fetch failed:', err))

    fetchUAVs()
      .then(setUAVs)
      .catch((err) => console.error('[WebSocketContext] UAVs fetch failed:', err))
  }, [])

  // Route incoming WebSocket messages to the correct state slice
  useEffect(() => {
    if (!lastMessage) return

    const { type, payload } = lastMessage

    if (type === 'telemetry_update') {
      setVictims((prev) => {
        const idx = prev.findIndex((v) => v.victim_id === payload.victim_id)
        if (idx === -1) return [...prev, payload]
        const updated = [...prev]
        updated[idx] = mergeVictimUpdate(updated[idx], payload)
        return updated
      })
      return
    }

    if (type === 'alert') {
      setAlerts((prev) => [payload, ...prev].slice(0, 100))
      return
    }

    if (type === 'uav_update') {
      setUAVs((prev) => {
        const idx = prev.findIndex((u) => u.uav_id === payload.uav_id)
        if (idx === -1) return [...prev, payload]
        const updated = [...prev]
        updated[idx] = { ...updated[idx], ...payload }
        return updated
      })
      return
    }
  }, [lastMessage])

  return (
    <WebSocketContext.Provider value={{ victims, alerts, uavs, connectionStatus }}>
      {children}
    </WebSocketContext.Provider>
  )
}

/**
 * useWebSocketContext — consume the shared WebSocket state.
 *
 * Must be called inside a component that is a descendant of
 * WebSocketProvider.
 *
 * @returns {{ victims: Array, alerts: Array, connectionStatus: string }}
 */
export function useWebSocketContext() {
  const ctx = useContext(WebSocketContext)
  if (!ctx) throw new Error('useWebSocketContext must be used inside WebSocketProvider')
  return ctx
}
