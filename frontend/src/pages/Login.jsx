import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import AuthShell from '../components/AuthShell'
import { Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(form.email, form.password)
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to continue your study plan."
      footer={<>Don&apos;t have an account? <Link to="/register" className="font-medium text-primary-600 hover:underline">Create one</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" required autoComplete="email" className="input"
            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" required autoComplete="current-password" className="input"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy}>
          {busy && <Spinner className="h-4 w-4 text-white" />} Log in
        </button>
      </form>
    </AuthShell>
  )
}
