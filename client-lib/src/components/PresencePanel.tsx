/**
 * PresencePanel — display-only panel showing camera feed and active faces.
 * For enrollment management use <EnrollmentSettings>.
 */
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { usePresenceSocket } from '../hooks/usePresenceSocket'
import { TrackList } from './TrackList'
import { VideoFeed } from './VideoFeed'

export interface PresencePanelProps {
  /** Show the active face list below the video. Default true. */
  showTrackList?: boolean
  /** Aspect ratio passed to VideoFeed. Default "4/3". */
  aspectRatio?: string
}

export function PresencePanel({ showTrackList = true, aspectRatio }: PresencePanelProps) {
  const tracks = usePresenceSocket()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      <VideoFeed aspectRatio={aspectRatio} />
      {showTrackList && (
        <Paper variant="outlined" sx={{ p: 1.5 }}>
          <Typography variant="caption" fontWeight={700} display="block" sx={{ mb: 0.5 }}>
            Active Faces
          </Typography>
          <TrackList tracks={tracks} />
        </Paper>
      )}
    </Box>
  )
}
