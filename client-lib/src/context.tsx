import { createContext, useContext, type ReactNode } from 'react'

export interface PresenceConfig {
  /**
   * Base URL of the Presence backend, e.g. "http://presence.local:8000".
   * Leave empty (default) when the library is served from the same origin as
   * the backend (i.e. the single-container deployment).
   */
  baseUrl: string
}

const PresenceContext = createContext<PresenceConfig>({ baseUrl: '' })

export function PresenceProvider({
  baseUrl = '',
  children,
}: {
  baseUrl?: string
  children: ReactNode
}) {
  return <PresenceContext.Provider value={{ baseUrl }}>{children}</PresenceContext.Provider>
}

export function usePresenceConfig(): PresenceConfig {
  return useContext(PresenceContext)
}

/** Convert an http(s) base URL to a ws(s) WebSocket URL + path. */
export function buildWsUrl(baseUrl: string, path: string): string {
  if (!baseUrl) {
    // Same-origin: derive from current page
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}${path}`
  }
  return baseUrl.replace(/^http/, 'ws') + path
}

/** Return the REST base for axios calls. */
export function buildHttpUrl(baseUrl: string, path: string): string {
  return (baseUrl || '') + path
}
