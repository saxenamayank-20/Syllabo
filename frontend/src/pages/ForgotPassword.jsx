import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { KeyRound } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import AuthShell from '../components/AuthShell'
import { Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const COOLDOWN_SECONDS = 60

export default function ForgotPassword() {
  const { user, resetPassword } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [step, setStep] = useState('email') // 'email' -> 'reset'
  const [email, setEmail] = useState('')
  const [form, setForm] = useState({ code: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (cooldown <= 0) return
    const id = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(id)
  }, [cooldown])

  if (user) return <Navigate to="/" replace />

  const sendCode = async (e) => {
    e?.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/auth/forgot-password', { email })
      if (!data.email_sent) {
        setError(data.message)
      } else {
        if (step === 'reset') toast.success('A new code is on its way')
        setStep('reset')
        setCooldown(COOLDOWN_SECONDS)
      }
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const submitReset = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) {
      setError('The two passwords do not match')
      return
    }
    setBusy(true)
    setError('')
    try {
      await resetPassword(email, form.code, form.password)
      toast.success('Password updated — you are logged in')
      navigate('/', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  const footer = <>Remembered it? <Link to="/login" className="font-medium text-primary-600 hover:underline">Back to log in</Link></>

  if (step === 'email') {
    return (
      <AuthShell title="Reset your password" subtitle="Enter your account email and we'll send you a 6-digit code." footer={footer}>
        <form onSubmit={sendCode} className="space-y-4">
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" type="email" required autoComplete="email" className="input" value={email}
              onChange={(e) => setEmail(e.target.value)} />
          </div>
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy && <Spinner className="h-4 w-4 text-white" />} Send reset code
          </button>
        </form>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Choose a new password" subtitle={`If an account exists for ${email}, we've emailed it a 6-digit code.`} footer={footer}>
      <div className="mb-5 flex items-center gap-3 rounded-xl bg-primary-50 px-4 py-3 text-sm text-primary-700">
        <KeyRound className="h-5 w-5 shrink-0" />
        <span className="min-w-0 break-words">{email}</span>
      </div>
      <form onSubmit={submitReset} className="space-y-4">
        <div>
          <label className="label" htmlFor="code">Reset code</label>
          <input id="code" inputMode="numeric" autoComplete="one-time-code" autoFocus required pattern="\d{6}" maxLength={6}
            placeholder="••••••" className="input text-center text-2xl font-semibold tracking-[0.5em]" value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value.replace(/\D/g, '').slice(0, 6) })} />
        </div>
        <div>
          <label className="label" htmlFor="new-password">New password</label>
          <input id="new-password" type="password" required minLength={6} maxLength={72} autoComplete="new-password" className="input"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </div>
        <div>
          <label className="label" htmlFor="confirm-password">Confirm new password</label>
          <input id="confirm-password" type="password" required minLength={6} maxLength={72} autoComplete="new-password" className="input"
            value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
        </div>
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy || form.code.length !== 6}>
          {busy && <Spinner className="h-4 w-4 text-white" />} Reset password
        </button>
        <button type="button" className="btn-secondary w-full" onClick={sendCode} disabled={busy || cooldown > 0}>
          {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
        </button>
      </form>
    </AuthShell>
  )
}
