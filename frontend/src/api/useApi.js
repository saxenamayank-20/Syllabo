import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from './client'
import { useToast } from '../context/ToastContext'

/** GET `path` on mount (and whenever it changes). Returns { data, loading, error, reload, setData }. */
export function useApi(path, initial = null) {
  const toast = useToast()
  const [data, setData] = useState(initial)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const reload = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) setLoading(true)
      try {
        const res = await api.get(path)
        setData(res.data)
        setError(null)
      } catch (err) {
        const msg = errorMessage(err)
        setError(msg)
        if (err.response?.status !== 401) toast.error(msg)
      } finally {
        setLoading(false)
      }
    },
    [path, toast],
  )

  useEffect(() => {
    reload()
  }, [reload])

  return { data, loading, error, reload, setData }
}
