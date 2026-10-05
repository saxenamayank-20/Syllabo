import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { MailCheck } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import AuthShell from '../components/AuthShell'
import { Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const COOLDOWN_SECONDS = 60

export default function VerifyEmail() {
  const { user, verifyEmail } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [params] = useSearchParams()
  const email = params.get('email') || location.state?.email || ''
  const [code, setCode] = useState('')
  const [error, setError] = useState(location.state?.email_sent === false ? location.state.message : '')
  const [busy, setBusy] = useState(false)
  const [resending, setResending] = useState(false)
  const [cooldown, setCooldown] = useState(COOLDOWN_SECONDS)

  useEffect(() => {
    if (cooldown <= 0) return
    const id = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(id)
  }, [cooldown])

  if (user) return <Navigate to="/" replace />
  if (!email) return <Navigate to="/register" replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await verifyEmail(email, code)
      toast.success('Email verified — welcome to StudyAI!')
      navigate('/', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  const resend = async () => {
    setResending(true)
    setError('')
    try {
      const { data } = await api.post('/auth/resend-code', { email })
      if (data.email_sent) toast.success('A new code is on its way')
      else setError(data.message)
      setCode('')
      setCooldown(COOLDOWN_SECONDS)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthShell
      title="Check your email"
      subtitle={location.state?.message && location.state.email_sent !== false ? location.state.message : `Enter the 6-digit code we sent to ${email}.`}
      footer={<>Wrong email? <Link to="/register" className="font-medium text-primary-600 hover:underline">Register again</Link></>}
    >
      <div className="mb-5 flex items-center gap-3 rounded-xl bg-primary-50 px-4 py-3 text-sm text-primary-700">
        <MailCheck className="h-5 w-5 shrink-0" />
        <span className="min-w-0 break-words">{email}</span>
      </div>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="code">Verification code</label>
          <input
            id="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            autoFocus
            required
            pattern="\d{6}"
            maxLength={6}
            placeholder="••••••"
            className="input text-center text-2xl font-semibold tracking-[0.5em]"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          />
          <p className="mt-1 text-xs text-slate-500">The code expires in 10 minutes. Check your spam folder too.</p>
        </div>
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
        <button type="submit" className="btn-primary w-full" disabled={busy || code.length !== 6}>
          {busy && <Spinner className="h-4 w-4 text-white" />} Verify email
        </button>
        <button type="button" className="btn-secondary w-full" onClick={resend} disabled={resending || cooldown > 0}>
          {resending && <Spinner className="h-4 w-4" />}
          {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
        </button>
      </form>
    </AuthShell>
  )
}
