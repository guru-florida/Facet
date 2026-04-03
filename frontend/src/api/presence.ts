import client from './client'
import type { Identity, PipelineStatus, Track } from './types'

export async function fetchPresence(): Promise<Track[]> {
  const { data } = await client.get<Track[]>('/presence')
  return data
}

export async function fetchIdentities(): Promise<Identity[]> {
  const { data } = await client.get<Identity[]>('/identities')
  return data
}

export async function createIdentity(name: string): Promise<Identity> {
  const { data } = await client.post<Identity>('/identities', { name })
  return data
}

export async function addIdentitySample(identityId: string): Promise<Identity> {
  const { data } = await client.post<Identity>(`/identities/${identityId}/samples`)
  return data
}

export async function deleteIdentity(identityId: string): Promise<void> {
  await client.delete(`/identities/${identityId}`)
}

export async function fetchStatus(): Promise<PipelineStatus> {
  const { data } = await client.get<PipelineStatus>('/status')
  return data
}
