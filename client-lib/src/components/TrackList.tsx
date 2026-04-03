import FaceIcon from '@mui/icons-material/Face'
import PersonIcon from '@mui/icons-material/Person'
import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemAvatar from '@mui/material/ListItemAvatar'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import type { Track } from '../types'

interface Props {
  tracks: Track[]
}

export function TrackList({ tracks }: Props) {
  const visible = tracks.filter((t) => !t.leftPending)

  if (visible.length === 0) {
    return (
      <Typography color="text.secondary" variant="body2" sx={{ py: 2, textAlign: 'center' }}>
        No faces detected
      </Typography>
    )
  }

  return (
    <List dense disablePadding>
      {visible.map((track) => (
        <ListItem key={track.trackId} disableGutters sx={{ py: 0.5 }}>
          <ListItemAvatar>
            <Avatar
              sx={{
                bgcolor: track.status === 'known' ? 'secondary.dark' : 'warning.dark',
                width: 36,
                height: 36,
              }}
            >
              {track.status === 'known' ? (
                <PersonIcon fontSize="small" />
              ) : (
                <FaceIcon fontSize="small" />
              )}
            </Avatar>
          </ListItemAvatar>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2" fontWeight={600}>
                  {track.displayName ?? 'Unknown'}
                </Typography>
                {track.stable && (
                  <Chip
                    label="stable"
                    size="small"
                    color="default"
                    sx={{ height: 16, fontSize: 10 }}
                  />
                )}
              </Box>
            }
            secondary={
              <Typography variant="caption" color="text.secondary">
                {track.status === 'known'
                  ? `${(track.confidence * 100).toFixed(0)}% match`
                  : `track #${track.trackId}`}
              </Typography>
            }
          />
        </ListItem>
      ))}
    </List>
  )
}
