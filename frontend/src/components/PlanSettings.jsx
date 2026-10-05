import { useEffect, useState } from 'react'
import { ChevronDown, Settings2 } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import { useApi } from '../api/useApi'
import { useToast } from '../context/ToastContext'
import { LoadingBlock, Spinner } from './ui'

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

/** Study preferences used by the AI planner: daily minutes, study days, goal. */
export default function PlanSettings({ defaultOpen = false }) {
  const toast = useToast()
  const prefs = useApi('/preferences')
  const [open, setOpen] = useState(defaultOpen)
  const [form, setForm] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (prefs.data) setForm({ ...prefs.data, days: prefs.data.study_days.split(',') })
  }, [prefs.data])

  const toggleDay = (day) =>
    setForm((f) => ({ ...f, days: f.days.includes(day) ? f.days.filter((d) => d !== day) : [...f.days, day] }))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.days.length) {
      toast.error('Choose at least one study day')
      return
    }
    setBusy(true)
    try {
      const { data } = await api.put('/preferences', {
        daily_study_minutes: Number(form.daily_study_minutes),
        study_days: DAYS.filter((d) => form.days.includes(d)).join(','),
        goal_note: form.goal_note,
      })
      prefs.setData(data)
      toast.success('Study settings saved')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const summary = prefs.data
    ? `${prefs.data.daily_study_minutes} min/day · ${prefs.data.study_days.split(',').join(', ')}`
    : ''

  return (
    <section className="card">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}
        className="flex w-full items-center gap-3 px-5 py-4 text-left">
        <Settings2 className="h-5 w-5 text-slate-500" />
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-slate-900">Study settings</h2>
          <p className="truncate text-xs text-slate-500">{summary || 'Used when generating AI plans'}</p>
        </div>
        <ChevronDown className={`h-5 w-5 text-slate-400 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="border-t border-slate-100 px-5 py-4">
          {!form ? (
            <LoadingBlock className="py-4" />
          ) : (
            <form onSubmit={submit} className="grid grid-cols-1 gap-4 md:grid-cols-[180px_1fr]">
              <div>
                <label className="label" htmlFor="pref-minutes">Daily study minutes</label>
                <input id="pref-minutes" type="number" min={15} max={960} step={15} required className="input"
                  value={form.daily_study_minutes} onChange={(e) => setForm({ ...form, daily_study_minutes: e.target.value })} />
              </div>
              <div>
                <span className="label">Study days</span>
                <div className="flex flex-wrap gap-2">
                  {DAYS.map((d) => {
                    const on = form.days.includes(d)
                    return (
                      <button key={d} type="button" onClick={() => toggleDay(d)} aria-pressed={on}
                        className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                          on ? 'border-primary-600 bg-primary-600 text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                        }`}>
                        {d}
                      </button>
                    )
                  })}
                </div>
              </div>
              <div className="md:col-span-2">
                <label className="label" htmlFor="pref-goal">Goal</label>
                <textarea id="pref-goal" rows={2} className="input" placeholder="e.g. Score 85%+ in finals, improve Physics"
                  value={form.goal_note} onChange={(e) => setForm({ ...form, goal_note: e.target.value })} />
              </div>
              <div className="md:col-span-2 flex justify-end">
                <button type="submit" className="btn-primary" disabled={busy}>
                  {busy && <Spinner className="h-4 w-4 text-white" />} Save settings
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </section>
  )
}
