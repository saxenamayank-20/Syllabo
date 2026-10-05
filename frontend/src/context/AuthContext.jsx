import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api, { getToken, setToken, setUnauthorizedHandler } from '../api/client'
import { browserTimeZone, setActiveTimeZone } from '../utils/date'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUserState] = useState(null)
  const [loading, setLoading] = useState(Boolean(getToken()))

  const setUser = useCallback((next) => {
    setActiveTimeZone(next?.timezone)
    setUserState(next)
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [setUser])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (!getToken()) return
    api
      .get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, [logout, setUser])

  /** Store a { access_token, user } response (login, verification, reset, password change). */
  const setSession = useCallback(
    (data) => {
      setToken(data.access_token)
      setUser(data.user)
      return data.user
    },
    [setUser],
  )

  const value = useMemo(
    () => ({
      user,
      loading,
      setUser,
      setSession,
      login: (email, password) => api.post('/auth/login', { email, password }).then((r) => setSession(r.data)),
      // Registration doesn't log in: it returns { email, email_sent, message } and the user must verify first.
      register: (name, email, password) =>
        api.post('/auth/register', { name, email, password, timezone: browserTimeZone() }).then((r) => r.data),
      verifyEmail: (email, code) => api.post('/auth/verify-email', { email, code }).then((r) => setSession(r.data)),
      resetPassword: (email, code, newPassword) =>
        api.post('/auth/reset-password', { email, code, new_password: newPassword }).then((r) => setSession(r.data)),
      logout,
    }),
    [user, loading, setUser, setSession, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
