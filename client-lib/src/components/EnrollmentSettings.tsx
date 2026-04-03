/**
 * EnrollmentSettings — self-contained identity enrollment and management panel.
 *
 * Includes video preview, enroll dialog, sample management, and identity list.
 * Requires <PresenceProvider> in the tree.
 */
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogTitle from '@mui/material/DialogTitle'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { useCallback, useEffect, useState } from 'react'
import { usePresenceApi } from '../api'
import type { Identity } from '../types'
import { VideoFeed } from './VideoFeed'

export interface EnrollmentSettingsProps {
  /** Hide the video preview (e.g. when embedding in a layout that shows it elsewhere) */
  hideVideo?: boolean
}

export function EnrollmentSettings({ hideVideo = false }: EnrollmentSettingsProps) {
  const api = usePresenceApi()
  const [identities, setIdentities] = useState<Identity[]>([])
  const [enrollOpen, setEnrollOpen] = useState(false)
  const [feedback, setFeedback] = useState<{ message: string; error?: boolean } | null>(null)

  const load = useCallback(async () => {
    try {
      setIdentities(await api.fetchIdentities())
    } catch {
      // backend may still be starting
    }
  }, [api])

  useEffect(() => {
    load()
  }, [load])

  const flash = (message: string, error = false) => {
    setFeedback({ message, error })
    setTimeout(() => setFeedback(null), 3500)
  }

  const handleCreated = (identity: Identity) => {
    setIdentities((prev) => [identity, ...prev])
    flash(`Enrolled "${identity.name}"`)
  }

  const handleAddSample = async (id: string) => {
    try {
      const updated = await api.addIdentitySample(id)
      setIdentities((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))
      flash('Sample added')
    } catch (err: unknown) {
      flash(err instanceof Error ? err.message : 'Failed to add sample', true)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete identity "${name}"?`)) return
    try {
      await api.deleteIdentity(id)
      setIdentities((prev) => prev.filter((i) => i.id !== id))
      flash(`Deleted "${name}"`)
    } catch {
      flash('Failed to delete', true)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {!hideVideo && <VideoFeed aspectRatio="4/3" />}

      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle2" fontWeight={700}>
            Enrolled Identities
          </Typography>
          <Button
            size="small"
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setEnrollOpen(true)}
          >
            Enroll
          </Button>
        </Box>

        {feedback && (
          <Typography
            variant="caption"
            color={feedback.error ? 'error' : 'primary'}
            display="block"
            sx={{ mb: 1 }}
          >
            {feedback.message}
          </Typography>
        )}

        <Divider sx={{ mb: 1 }} />

        {identities.length === 0 ? (
          <Typography color="text.secondary" variant="body2" sx={{ py: 2, textAlign: 'center' }}>
            No identities enrolled yet
          </Typography>
        ) : (
          <List dense disablePadding>
            {identities.map((identity) => (
              <ListItem
                key={identity.id}
                disableGutters
                secondaryAction={
                  <Box>
                    <Tooltip title="Add face sample">
                      <IconButton size="small" onClick={() => handleAddSample(identity.id)}>
                        <PersonAddIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete identity">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(identity.id, identity.name)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <ListItemText
                  primary={identity.name}
                  secondary={`${identity.sampleCount} sample${identity.sampleCount !== 1 ? 's' : ''}`}
                />
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      <EnrollDialog
        open={enrollOpen}
        onClose={() => setEnrollOpen(false)}
        onCreated={handleCreated}
        onError={(msg) => flash(msg, true)}
      />
    </Box>
  )
}

// ── Internal enroll dialog ────────────────────────────────────────────────────

interface EnrollDialogProps {
  open: boolean
  onClose: () => void
  onCreated: (identity: Identity) => void
  onError: (message: string) => void
}

function EnrollDialog({ open, onClose, onCreated, onError }: EnrollDialogProps) {
  const api = usePresenceApi()
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const identity = await api.createIdentity(name.trim())
      onCreated(identity)
      setName('')
      onClose()
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Enroll failed — ensure a face is visible and stable in the frame.'
      setError(msg)
      onError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setName('')
    setError(null)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Enroll New Identity</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Position your face in the camera frame, enter a name, then click Capture.
        </DialogContentText>
        <TextField
          autoFocus
          fullWidth
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          error={!!error}
          helperText={error ?? ' '}
          disabled={loading}
          size="small"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading || !name.trim()}>
          {loading ? 'Capturing…' : 'Capture'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
