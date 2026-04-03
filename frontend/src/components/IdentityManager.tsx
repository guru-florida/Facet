import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import PersonAddIcon from '@mui/icons-material/PersonAdd'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { useCallback, useEffect, useState } from 'react'
import { addIdentitySample, deleteIdentity, fetchIdentities } from '../api/presence'
import type { Identity } from '../api/types'
import EnrollDialog from './EnrollDialog'

export default function IdentityManager() {
  const [identities, setIdentities] = useState<Identity[]>([])
  const [enrollOpen, setEnrollOpen] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setIdentities(await fetchIdentities())
    } catch {
      // silently ignore — backend may still be starting
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleCreated = (identity: Identity) => {
    setIdentities((prev) => [identity, ...prev])
    showFeedback(`Enrolled "${identity.name}"`)
  }

  const handleAddSample = async (id: string) => {
    try {
      const updated = await addIdentitySample(id)
      setIdentities((prev) => prev.map((i) => (i.id === updated.id ? updated : i)))
      showFeedback('Sample added')
    } catch (err: unknown) {
      showFeedback(err instanceof Error ? err.message : 'Failed to add sample')
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete identity "${name}"?`)) return
    try {
      await deleteIdentity(id)
      setIdentities((prev) => prev.filter((i) => i.id !== id))
      showFeedback(`Deleted "${name}"`)
    } catch {
      showFeedback('Failed to delete')
    }
  }

  const showFeedback = (msg: string) => {
    setFeedback(msg)
    setTimeout(() => setFeedback(null), 3000)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle2" fontWeight={700}>
          Known Identities
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
        <Typography variant="caption" color="primary" sx={{ display: 'block', mb: 1 }}>
          {feedback}
        </Typography>
      )}

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

      <EnrollDialog
        open={enrollOpen}
        onClose={() => setEnrollOpen(false)}
        onCreated={handleCreated}
      />
    </Box>
  )
}
