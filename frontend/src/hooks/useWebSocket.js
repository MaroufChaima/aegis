import { useEffect, useRef, useState, useCallback } from 'react'

const MAX_ATTEMPTS  = 5
const BASE_DELAY_MS = 3000  // 3 s base — doubles on each retry (exponential backoff)

/**
 * useWebSocket — manages a single WebSocket connection to the backend.
 *
 * Reconnection strategy:
 *   - On disconnect (intentional or network drop), waits BASE_DELAY_MS * 2^attempt ms
 *     before the next attempt, up to MAX_ATTEMPTS retries.
 *   - Stops retrying after MAX_ATTEMPTS failures and sets status to "failed".
 *   - A successful connection resets the attempt counter.
 *
 * @param {string} url  Full WebSocket URL, e.g. "ws://localhost:8000/ws"
 * @returns {{
 *   lastMessage:       object|null,   parsed JSON from the last received frame
 *   connectionStatus:  string         "connecting"|"connected"|"disconnected"|"failed"
 * }}
 */
export default function useWebSocket(url) {
  const [lastMessage,      setLastMessage]      = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('connecting')

  const wsRef      = useRef(null)   // active WebSocket instance
  const attemptRef = useRef(0)      // reconnect attempt counter
  const timerRef   = useRef(null)   // reconnect delay timer

  const connect = useCallback(() => {
    // Clean up any existing socket before opening a new one
    if (wsRef.current) {
      wsRef.current.onclose = null  // prevent recursive reconnect on manual close
      wsRef.current.close()
    }

    setConnectionStatus('connecting')
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      attemptRef.current = 0
      setConnectionStatus('connected')
    }

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setLastMessage(parsed)
      } catch {
        // Ignore non-JSON frames
      }
    }

    ws.onclose = () => {
      setConnectionStatus('disconnected')
      const attempt = attemptRef.current

      if (attempt >= MAX_ATTEMPTS) {
        setConnectionStatus('failed')
        return
      }

      const delay = BASE_DELAY_MS * Math.pow(2, attempt)
      attemptRef.current = attempt + 1
      timerRef.current = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      // onclose fires after onerror — reconnect logic lives there
      ws.close()
    }
  }, [url])

  useEffect(() => {
    connect()

    return () => {
      // Cleanup on unmount — stop reconnect timers and close socket
      clearTimeout(timerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect])

  return { lastMessage, connectionStatus }
}
