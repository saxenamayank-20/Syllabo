import { useMemo, useState } from 'react'
import { BadgeCheck, KeyRound, UserRound } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import PlanSettings from '../components/PlanSettings'
import { CardHeader, PageHeader, Spinner } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { browserTimeZone } from '../utils/date'

function timeZoneOptions(current) {
  let zones = []
  try {
    zones = Intl.supportedValuesOf('timeZone')
  } catch {
    zones = []
  }
  return [...new Set(['UTC', current, browserTimeZone(), ...zones])].filter(Boolean).sort()
}

// same offset right now? (e.g. Asia/Calcutta vs Asia/Kolkata)
function sameOffset(a, b) {
  const offset = (zone) => {
    try {
      return new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'longOffset' }).format(new Date()).split(' ').pop()
    } catch {
      return zone
    }
  }
  return offset(a) === offset(b)
}

function ProfileCard() {
  const { user, setUser } = useAuth()
  const toast = useToast()
  const [form, setForm] = useState({ name: user.name, timezone: user.timezone })
  const [busy, setBusy] = useState(false)
  const zones = useMemo(() => timeZoneOptions(user.timezone), [user.timezone])
  const deviceZone = browserTimeZone()
  const dirty = form.name.trim() !== user.name || form.timezone !== user.timezone

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const { data } = await api.patch('/auth/me', { name: form.name.trim(), timezone: form.timezone })
      setUser(data)
      toast.success('Profile saved')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card p-5">
      <CardHeader title="Profile" icon={UserRound} />
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="profile-name">Full name</label>
          <input id="profile-name" className="input" required maxLength={120} value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <span className="label">Email</span>
          <p className="flex items-center gap-2 text-sm text-slate-700">
            {user.email}
            {user.email_verified && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 dark:bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300">
                <BadgeCheck className="h-3.5 w-3.5" /> Verified
              </span>
            )}
          </p>
        </div>
        <div>
          <label className="label" htmlFor="profile-tz">Timezone</label>
          <select id="profile-tz" className="input" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })}>
            {zones.map((z) => <option key={z} value={z}>{z.replaceAll('_', ' ')}</option>)}
          </select>
          <p className="mt-1 text-xs text-slate-500">
            Decides what &quot;today&quot; means for your tasks and exam countdown.
            {!sameOffset(form.timezone, deviceZone) && (
              <> <button type="button" className="font-medium text-primary-600 dark:text-primary-400 hover:underline"
                onClick={() => setForm({ ...form, timezone: deviceZone })}>Use this device&apos;s timezone ({deviceZone})</button></>
            )}
          </p>
        </div>
        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={busy || !dirty}>
            {busy && <Spinner className="h-4 w-4 text-white" />} Save profile
          </button>
        </div>
      </form>
    </section>
  )
}

function PasswordCard() {
  const { setSession } = useAuth()
  const toast = useToast()
  const empty = { current: '', next: '', confirm: '' }
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (form.next !== form.confirm) {
      setError('The two new passwords do not match')
      return
    }
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/auth/change-password', { current_password: form.current, new_password: form.next })
      setSession(data)
      setForm(empty)
      toast.success('Password changed. Other devices have been logged out.')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card p-5">
      <CardHeader title="Change password" icon={KeyRound} />
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="pw-current">Current password</label>
          <input id="pw-current" type="password" required autoComplete="current-password" className="input" value={form.current} onChange={set('current')} />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="pw-new">New password</label>
            <input id="pw-new" type="password" required minLength={6} maxLength={72} autoComplete="new-password" className="input" value={form.next} onChange={set('next')} />
          </div>
          <div>
            <label className="label" htmlFor="pw-confirm">Confirm new password</label>
            <input id="pw-confirm" type="password" required minLength={6} maxLength={72} autoComplete="new-password" className="input" value={form.confirm} onChange={set('confirm')} />
          </div>
        </div>
        {error && <p className="rounded-lg bg-red-50 dark:bg-red-500/10 px-3 py-2 text-sm text-red-700 dark:text-red-300" role="alert">{error}</p>}
        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={busy}>
            {busy && <Spinner className="h-4 w-4 text-white" />} Change password
          </button>
        </div>
      </form>
    </section>
  )
}

export default function Settings() {
  return (
    <div className="space-y-6">
      <PageHeader title="Settings" subtitle="Manage your profile, password and study preferences." />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ProfileCard />
        <PasswordCard />
      </div>
      <PlanSettings defaultOpen />
    </div>
  )
}
