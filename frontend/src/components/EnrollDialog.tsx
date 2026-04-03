import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogTitle from '@mui/material/DialogTitle'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { createIdentity } from '../api/presence'
import type { Identity } from '../api/types'

interface Props {
  open: boolean
  onClose: () => void
  onCreated: (identity: Identity) => void
}

export default function EnrollDialog({ open, onClose, onCreated }: Props) {
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
      const identity = await createIdentity(name.trim())
      onCreated(identity)
      setName('')
      onClose()
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Failed to enroll — ensure a face is visible and stable in the frame.'
      setError(msg)
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
          Position your face in the camera frame, then enter a name and click Capture.
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
