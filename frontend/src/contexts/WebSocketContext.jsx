import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import useWebSocket from '../hooks/useWebSocket'
import { fetchVictims } from '../api/victims'
import { WS_URL } from '../utils/constants'

const WebSocketContext = createContext(null)

/**
 * WebSocketProvider — connects to the backend WebSocket and maintains
 * the live state of victims and alerts for the entire dashboard.
 *
 * Message routing:
 *   "telemetry_update" → upserts the device in the victims array
 *                         (replaces existing entry by device_id,
 *                          appends if new)
 *   "alert"            → prepends the alert to the alerts array,
 *                         keeping at most 100 entries
 *
 * On mount, fetches the current device list from REST so the table
 * and map populate immediately before the first WebSocket message arrives.
 *
 * @param {{ children: React.ReactNode }} props
 */
export function WebSocketProvider({ children }) {
  const [victims, setVictims] = useState([])
  const [alerts,  setAlerts]  = useState([])

  const { lastMessage, connectionStatus } = useWebSocket(WS_URL)

  // Seed victims from REST on first load
  useEffect(() => {
    fetchVictims()
      .then(setVictims)
      .catch((err) => console.error('[WebSocketContext] Initial fetch failed:', err))
  }, [])

  // Route incoming WebSocket messages to the correct state update
  useEffect(() => {
    if (!lastMessage) return

    const { type, payload } = lastMessage

    if (type === 'telemetry_update') {
      setVictims((prev) => {
        const idx = prev.findIndex((v) => v.device_id === payload.device_id)
        if (idx === -1) return [...prev, payload]
        const updated = [...prev]
        updated[idx] = { ...updated[idx], ...payload }
        return updated
      })
      return
    }

    if (type === 'alert') {
      // Prepend; cap list at 100 so the feed doesn't grow unbounded
      setAlerts((prev) => [payload, ...prev].slice(0, 100))
      return
    }
  }, [lastMessage])

  return (
    <WebSocketContext.Provider value={{ victims, alerts, connectionStatus }}>
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
