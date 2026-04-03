import { useEffect, useRef, useState } from 'react'
import type { PresenceEvent, Track } from '../api/types'

const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/presence`

export function usePresenceSocket(): Track[] {
  const [tracks, setTracks] = useState<Map<string, Track>>(new Map())
  const wsRef = useRef<WebSocket | null>(null)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let alive = true

    function connect() {
      if (!alive) return

      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onmessage = (evt: MessageEvent<string>) => {
        const event = JSON.parse(evt.data) as PresenceEvent

        if (event.type === 'ping') return
console.log('tracks', event);
        setTracks((prev) => {
          // Snapshot replaces the entire map — syncs state after reconnect
          if (event.type === 'snapshot') {
            const next = new Map<string, Track>()
            for (const track of event.tracks) next.set(track.trackId, track)
            return next
          }

          const next = new Map(prev)
          if (event.type === 'track_added' || event.type === 'track_updated') {
            next.set(event.track.trackId, event.track)
          } else if (event.type === 'track_removed') {
            next.delete(event.trackId)
          }
          return next
        })
      }

      ws.onclose = () => {
        if (alive) {
          retryTimer.current = setTimeout(connect, 2000)
        }
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      alive = false
      if (retryTimer.current) clearTimeout(retryTimer.current)
      // Only close if the socket is open or connecting — avoids the
      // "closed before connection established" warning in React StrictMode.
      const ws = wsRef.current
      if (ws && ws.readyState !== WebSocket.CLOSED) ws.close()
    }
  }, [])

  return Array.from(tracks.values())
}
