import { useState } from 'react'
import api, { errorMessage } from './client'
import { useToast } from '../context/ToastContext'

/** Toggle a task's status with an optimistic update. `setTasks` updates the local list. */
export function useTaskToggle(setTasks, onChanged) {
  const toast = useToast()
  const [busyId, setBusyId] = useState(null)

  const toggle = async (task) => {
    const status = task.status === 'completed' ? 'pending' : 'completed'
    const apply = (s) => setTasks((list) => list.map((t) => (t.id === task.id ? { ...t, status: s } : t)))
    apply(status)
    setBusyId(task.id)
    try {
      await api.patch(`/tasks/${task.id}/status`, { status })
      onChanged?.()
    } catch (err) {
      apply(task.status)
      toast.error(errorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  return { toggle, busyId }
}
