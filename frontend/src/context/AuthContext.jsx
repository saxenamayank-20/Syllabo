import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api, { getToken, setToken, setUnauthorizedHandler } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(getToken()))

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (!getToken()) return
    api
      .get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, [logout])

  // Login and email verification both return { access_token, user }.
  const authenticate = useCallback(async (path, payload) => {
    const { data } = await api.post(path, payload)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      login: (email, password) => authenticate('/auth/login', { email, password }),
      // Registration doesn't log in: it returns { email, email_sent, message } and the user must verify first.
      register: (name, email, password) => api.post('/auth/register', { name, email, password }).then((r) => r.data),
      verifyEmail: (email, code) => authenticate('/auth/verify-email', { email, code }),
      logout,
    }),
    [user, loading, authenticate, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
