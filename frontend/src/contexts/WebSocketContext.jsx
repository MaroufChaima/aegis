import { useContext, useEffect, useState, createContext, useCallback } from 'react'
import useWebSocket from '../hooks/useWebSocket'
import { fetchVictims } from '../api/victims'
import { fetchUAVs } from '../api/uavs'
import { fetchRescueTeams } from '../api/rescueTeams'
import { WS_URL } from '../utils/constants'
import { DEFAULT_REGION } from '../utils/regions'

const WebSocketContext = createContext(null)

const PRESERVE_IF_NULL = [
  'name', 'age', 'gender', 'risk_category', 'medical_conditions',
  'is_athlete', 'pregnancy_status', 'height_cm', 'weight_kg', 'home_region',
  'current_region', 'emergency_status', 'altitude_m', 'uav_backup_ids',
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

export function WebSocketProvider({ children }) {
  const [region, setRegion] = useState(DEFAULT_REGION)
  const [victims, setVictims] = useState([])
  const [alerts, setAlerts] = useState([])
  const [uavs, setUAVs] = useState([])
  const [teams, setTeams] = useState([])

  const { lastMessage, connectionStatus } = useWebSocket(WS_URL)

  const refreshRegionData = useCallback(async (regionKey) => {
    const [v, u, t] = await Promise.all([
      fetchVictims(regionKey),
      fetchUAVs(regionKey),
      fetchRescueTeams(regionKey),
    ])
    setVictims(v)
    setUAVs(u)
    setTeams(t)
  }, [])

  useEffect(() => {
    refreshRegionData(region).catch((err) => console.error('[WebSocketContext] Region fetch failed:', err))
  }, [region, refreshRegionData])

  useEffect(() => {
    if (!lastMessage) return
    const { type, payload } = lastMessage

    if (type === 'telemetry_update') {
      if (payload.home_region && payload.home_region !== region && payload.current_region !== region) return
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
      const uavRegion = payload.current_region || payload.home_region
      if (uavRegion && uavRegion !== region) return
      setUAVs((prev) => {
        const idx = prev.findIndex((u) => u.uav_id === payload.uav_id)
        if (idx === -1) return [...prev, payload]
        const updated = [...prev]
        updated[idx] = { ...updated[idx], ...payload }
        return updated
      })
    }
  }, [lastMessage, region])

  return (
    <WebSocketContext.Provider value={{
      victims, alerts, uavs, teams, region, setRegion, connectionStatus, refreshRegionData,
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocketContext() {
  const ctx = useContext(WebSocketContext)
  if (!ctx) throw new Error('useWebSocketContext must be used inside WebSocketProvider')
  return ctx
}
