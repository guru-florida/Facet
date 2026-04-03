import { useEffect, useRef, useState } from 'react'
import { buildWsUrl, usePresenceConfig } from '../context'

export function useVideoSocket(): string | null {
  const { baseUrl } = usePresenceConfig()
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const prevUrl = useRef<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const url = buildWsUrl(baseUrl, '/ws/video')
    let alive = true

    function connect() {
      if (!alive) return
      const ws = new WebSocket(url)
      ws.binaryType = 'arraybuffer'
      wsRef.current = ws

      ws.onmessage = (evt: MessageEvent<ArrayBuffer>) => {
        const blob = new Blob([evt.data], { type: 'image/jpeg' })
        const next = URL.createObjectURL(blob)
        setBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return next
        })
        prevUrl.current = next
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
      if (prevUrl.current) URL.revokeObjectURL(prevUrl.current)
    }
  }, [baseUrl])

  return blobUrl
}
