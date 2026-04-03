import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import Typography from '@mui/material/Typography'
import { useEffect, useState } from 'react'
import { fetchStatus } from '../api/presence'
import type { PipelineStatus } from '../api/types'

export default function StatusBar() {
  const [status, setStatus] = useState<PipelineStatus | null>(null)

  useEffect(() => {
    const poll = async () => {
      try {
        setStatus(await fetchStatus())
      } catch {
        // backend may not be ready yet
      }
    }
    poll()
    const interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      <Chip
        label={status?.running ? 'Running' : 'Stopped'}
        color={status?.running ? 'success' : 'error'}
        size="small"
        variant="outlined"
      />
      {status && (
        <>
          <Typography variant="caption" color="text.secondary">
            {status.fps} fps
          </Typography>
          <Typography variant="caption" color="text.secondary">
            ·
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {status.trackCount} track{status.trackCount !== 1 ? 's' : ''}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            ·
          </Typography>
          <Chip
            label={status.recognizerReady ? 'Recognizer ready' : 'Recognizer loading…'}
            color={status.recognizerReady ? 'default' : 'warning'}
            size="small"
            variant="outlined"
          />
        </>
      )}
    </Box>
  )
}
