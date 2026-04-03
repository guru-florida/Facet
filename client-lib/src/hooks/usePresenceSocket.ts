import { useEffect, useRef, useState } from 'react'
import { buildWsUrl, usePresenceConfig } from '../context'
import type { PresenceEvent, Track } from '../types'

export function usePresenceSocket(): Track[] {
  const { baseUrl } = usePresenceConfig()
  const [tracks, setTracks] = useState<Map<string, Track>>(new Map())
  const wsRef = useRef<WebSocket | null>(null)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const url = buildWsUrl(baseUrl, '/ws/presence')
    let alive = true

    function connect() {
      if (!alive) return
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onmessage = (evt: MessageEvent<string>) => {
        const event = JSON.parse(evt.data) as PresenceEvent
        if (event.type === 'ping') return

        setTracks((prev) => {
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
        if (alive) retryTimer.current = setTimeout(connect, 2000)
      }
      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      alive = false
      if (retryTimer.current) clearTimeout(retryTimer.current)
      const ws = wsRef.current
      if (ws && ws.readyState !== WebSocket.CLOSED) ws.close()
    }
  }, [baseUrl])

  return Array.from(tracks.values())
}
