// Provider — wrap your app (or the relevant subtree) with this
export { PresenceProvider } from './context'

// Hooks — use independently if you don't need the components
export { usePresenceSocket } from './hooks/usePresenceSocket'
export { useVideoSocket } from './hooks/useVideoSocket'

// API — direct REST calls bound to the configured base URL
export { usePresenceApi } from './api'

// Components
export { VideoFeed } from './components/VideoFeed'
export { TrackList } from './components/TrackList'
export { EnrollmentSettings } from './components/EnrollmentSettings'
export { PresencePanel } from './components/PresencePanel'

// Types
export type {
  BBox,
  Identity,
  PingEvent,
  PipelineStatus,
  PresenceEvent,
  SnapshotEvent,
  Track,
  TrackAddedEvent,
  TrackRemovedEvent,
  TrackStatus,
  TrackUpdatedEvent,
} from './types'
