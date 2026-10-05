import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import AuthShell from '../components/AuthShell'
import { Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const pending = await register(form.name, form.email, form.password)
      navigate(`/verify-email?email=${encodeURIComponent(pending.email)}`, { state: pending })
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  const field = (key) => ({ value: form[key], onChange: (e) => setForm({ ...form, [key]: e.target.value }) })

  return (
    <AuthShell
      title="Create your account"
      subtitle="Plan smarter, track progress and hit your targets."
      footer={<>Already have an account? <Link to="/login" className="font-medium text-primary-600 hover:underline">Log in</Link></>}
    >
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="name">Full name</label>
          <input id="name" required autoComplete="name" className="input" {...field('name')} />
        </div>
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" required autoComplete="email" className="input" {...field('email')} />
          <p className="mt-1 text-xs text-slate-500">Use your real email — we&apos;ll send a code to verify it.</p>
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" required minLength={6} maxLength={72} autoComplete="new-password"
            className="input" {...field('password')} />
          <p className="mt-1 text-xs text-slate-500">At least 6 characters.</p>
        </div>
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy}>
          {busy && <Spinner className="h-4 w-4 text-white" />} Create account
        </button>
      </form>
    </AuthShell>
  )
}
