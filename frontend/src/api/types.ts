export interface BBox {
  x: number
  y: number
  w: number
  h: number
}

export type TrackStatus = 'unknown' | 'known'

export interface Track {
  trackId: string
  status: TrackStatus
  identityId: string | null
  displayName: string | null
  confidence: number
  firstSeenAt: string
  lastSeenAt: string
  bbox: BBox
  stable: boolean
  leftPending: boolean
}

export interface Identity {
  id: string
  name: string
  createdAt: string
  sampleCount: number
}

export interface PipelineStatus {
  running: boolean
  fps: number
  frameCount: number
  trackCount: number
  recognizerReady: boolean
}

export interface TrackAddedEvent {
  type: 'track_added'
  track: Track
}

export interface TrackUpdatedEvent {
  type: 'track_updated'
  track: Track
}

export interface TrackRemovedEvent {
  type: 'track_removed'
  trackId: string
}

export interface SnapshotEvent {
  type: 'snapshot'
  tracks: Track[]
}

export interface PingEvent {
  type: 'ping'
}

export type PresenceEvent =
  | TrackAddedEvent
  | TrackUpdatedEvent
  | TrackRemovedEvent
  | SnapshotEvent
  | PingEvent
