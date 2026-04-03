import Box from '@mui/material/Box'
import Divider from '@mui/material/Divider'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import IdentityManager from './components/IdentityManager'
import StatusBar from './components/StatusBar'
import TrackList from './components/TrackList'
import VideoFeed from './components/VideoFeed'
import { usePresenceSocket } from './hooks/usePresenceSocket'

export default function App() {
  const tracks = usePresenceSocket()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        p: { xs: 2, md: 3 },
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" fontWeight={700} letterSpacing={1}>
          Presence
        </Typography>
        <StatusBar />
      </Box>

      {/* Main grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '3fr 2fr' },
          gap: 2,
          flex: 1,
        }}
      >
        {/* Left: Video + active faces */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <VideoFeed />
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
              Active Faces
            </Typography>
            <TrackList tracks={tracks} />
          </Paper>
        </Box>

        {/* Right: Identity management */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Paper sx={{ p: 2, flex: 1 }}>
            <IdentityManager />
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              API Endpoints
            </Typography>
            <Divider sx={{ mb: 1 }} />
            {[
              'GET  /api/presence',
              'GET  /api/identities',
              'POST /api/identities',
              'POST /api/identities/:id/samples',
              'DEL  /api/identities/:id',
              'GET  /api/status',
              'WS   /ws/presence',
              'WS   /ws/video',
            ].map((endpoint) => (
              <Typography key={endpoint} variant="caption" display="block" color="text.secondary" fontFamily="monospace">
                {endpoint}
              </Typography>
            ))}
          </Paper>
        </Box>
      </Box>
    </Box>
  )
}
