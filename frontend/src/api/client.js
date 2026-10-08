import axios from 'axios'

const TOKEN_KEY = 'studyai_token'

// token in memory + localStorage so it survives a reload
let accessToken = localStorage.getItem(TOKEN_KEY)
let onUnauthorized = () => {}

export function setToken(token) {
  accessToken = token
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function getToken() {
  return accessToken
}

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthCall = ['/auth/login', '/auth/register', '/auth/verify-email', '/auth/resend-code', '/auth/forgot-password', '/auth/reset-password', '/auth/change-password'].some((p) =>
      error.config?.url?.startsWith(p),
    )
    if (error.response?.status === 401 && !isAuthCall && accessToken) {
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

// axios error -> readable message
export function errorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (!error?.response) return 'Cannot reach the server. It may be waking up — please try again in a few seconds.'
  const detail = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && !Array.isArray(detail) && detail.message) return detail.message
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d) => {
        const field = d.loc?.filter((p) => p !== 'body').join('.')
        const msg = d.msg?.replace(/^Value error, /, '')
        return field ? `${field}: ${msg}` : msg
      })
      .join('; ')
  }
  return fallback
}

export default api

// login refused because the email isn't verified yet
export function isEmailNotVerified(error) {
  return error?.response?.status === 403 && error.response.data?.detail?.code === 'email_not_verified'
}
