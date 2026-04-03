import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { useVideoSocket } from '../hooks/useVideoSocket'

export default function VideoFeed() {
  const blobUrl = useVideoSocket()

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        aspectRatio: '4/3',
        bgcolor: '#000',
        borderRadius: 2,
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {blobUrl ? (
        <Box
          component="img"
          src={blobUrl}
          alt="Camera feed"
          sx={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        />
      ) : (
        <Typography color="text.secondary" variant="body2">
          Connecting to camera…
        </Typography>
      )}
    </Box>
  )
}
