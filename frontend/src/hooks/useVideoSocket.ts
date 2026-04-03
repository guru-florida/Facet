import { useEffect, useRef, useState } from 'react'

const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/video`

export function useVideoSocket(): string | null {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const prevUrl = useRef<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let alive = true

    function connect() {
      if (!alive) return
      const ws = new WebSocket(WS_URL)
      ws.binaryType = 'arraybuffer'
      wsRef.current = ws

      ws.onmessage = (evt: MessageEvent<ArrayBuffer>) => {
        const blob = new Blob([evt.data], { type: 'image/jpeg' })
        const url = URL.createObjectURL(blob)
        setBlobUrl((prev) => {
          if (prev) URL.revokeObjectURL(prev)
          return url
        })
        prevUrl.current = url
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
      const ws = wsRef.current
      if (ws && ws.readyState !== WebSocket.CLOSED) ws.close()
      if (prevUrl.current) URL.revokeObjectURL(prevUrl.current)
    }
  }, [])

  return blobUrl
}
