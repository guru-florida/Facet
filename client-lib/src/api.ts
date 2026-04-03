import axios from 'axios'
import { useMemo } from 'react'
import { buildHttpUrl, usePresenceConfig } from './context'
import type { Identity, PipelineStatus, Track } from './types'

function createClient(baseUrl: string) {
  return axios.create({ baseURL: buildHttpUrl(baseUrl, '/api') })
}

export interface PresenceApi {
  fetchPresence(): Promise<Track[]>
  fetchIdentities(): Promise<Identity[]>
  createIdentity(name: string): Promise<Identity>
  addIdentitySample(identityId: string): Promise<Identity>
  deleteIdentity(identityId: string): Promise<void>
  fetchStatus(): Promise<PipelineStatus>
}

export function usePresenceApi(): PresenceApi {
  const { baseUrl } = usePresenceConfig()

  return useMemo(() => {
    const http = createClient(baseUrl)
    return {
      fetchPresence: () => http.get<Track[]>('/presence').then((r) => r.data),
      fetchIdentities: () => http.get<Identity[]>('/identities').then((r) => r.data),
      createIdentity: (name) => http.post<Identity>('/identities', { name }).then((r) => r.data),
      addIdentitySample: (id) =>
        http.post<Identity>(`/identities/${id}/samples`).then((r) => r.data),
      deleteIdentity: (id) => http.delete(`/identities/${id}`).then(() => undefined),
      fetchStatus: () => http.get<PipelineStatus>('/status').then((r) => r.data),
    }
  }, [baseUrl])
}
