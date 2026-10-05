import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw, Sparkles } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { addDaysISO, formatDayHeading, formatDuration, formatTime, toISODate } from '../utils/date'
import { Modal, Spinner, SubjectDot } from './ui'

const defaultRange = () => ({ start_date: toISODate(), end_date: addDaysISO(6) })

function Preview({ preview }) {
  const total = preview.days.reduce((n, d) => n + d.tasks.length, 0)
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        <span className="font-medium text-slate-900">{total} tasks</span> across {preview.days.length} study days
        (limit {preview.daily_study_minutes} min/day).
      </p>
      {preview.replaces_pending_ai_tasks > 0 && (
        <p className="flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          Saving will replace {preview.replaces_pending_ai_tasks} pending AI task(s) already in this date range.
          Your manual and completed tasks are kept.
        </p>
      )}
      <div className="max-h-[45vh] space-y-3 overflow-y-auto pr-1">
        {preview.days.map((day) => (
          <div key={day.date} className="rounded-xl border border-slate-100 p-3">
            <div className="mb-1 flex items-baseline justify-between gap-2">
              <p className="text-sm font-semibold text-slate-900">{formatDayHeading(day.date)}</p>
              <p className="text-xs text-slate-500">
                {day.available_mins
                  ? `${formatDuration(day.total_mins)} planned · ${formatDuration(day.available_mins)} free`
                  : 'Day already full'}
              </p>
            </div>
            {!day.tasks.length ? (
              <p className="py-1 text-xs text-slate-400">No AI tasks for this day.</p>
            ) : (
              <ul className="divide-y divide-slate-50">
                {day.tasks.map((t, i) => (
                  <li key={i} className="flex items-center gap-3 py-2">
                    <span className="w-16 shrink-0 text-xs text-slate-500">{formatTime(t.start_time)}</span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm text-slate-800">{t.title}</p>
                      <p className="flex items-center gap-1.5 text-xs text-slate-500">
                        <SubjectDot color={t.subject_color} /> {t.subject_name}
                        {t.topic_name && <> · {t.topic_name}</>}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-slate-500">{formatDuration(t.duration_mins)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      {preview.skipped.length > 0 && (
        <details className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
          <summary className="cursor-pointer font-medium">{preview.skipped.length} suggestion(s) skipped</summary>
          <ul className="mt-2 space-y-1">
            {preview.skipped.map((s, i) => (
              <li key={i}><span className="text-slate-800">{s.date} · {s.title}</span> — {s.reason}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

/** Date range → Gemini preview → Save / Regenerate / Cancel. Gemini is only called on button click. */
export default function GeneratePlanModal({ open, onClose, onSaved }) {
  const toast = useToast()
  const [range, setRange] = useState(defaultRange)
  const [preview, setPreview] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open) {
      setRange(defaultRange())
      setPreview(null)
      setError('')
    }
  }, [open])

  const generate = async (e) => {
    e?.preventDefault()
    setGenerating(true)
    setError('')
    try {
      const { data } = await api.post('/ai/generate-plan', range)
      setPreview(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setGenerating(false)
    }
  }

  const save = async () => {
    setSaving(true)
    try {
      const { data } = await api.post('/ai/save-plan', {
        start_date: preview.start_date,
        end_date: preview.end_date,
        days: preview.days.map((d) => ({
          date: d.date,
          tasks: d.tasks.map(({ subject_id, topic_id, title, start_time, duration_mins }) => ({
            subject_id, topic_id, title, start_time, duration_mins,
          })),
        })),
      })
      toast.success(`AI plan saved — ${data.tasks_created} task(s) added`)
      onSaved()
      onClose()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const close = () => !generating && !saving && onClose()
  const busy = generating || saving
  const hasTasks = preview?.days.some((d) => d.tasks.length)

  return (
    <Modal open={open} wide title={preview ? 'Review your AI plan' : 'Generate AI study plan'} onClose={close}
      footer={
        preview ? (
          <>
            <button className="btn-secondary" onClick={close} disabled={busy}>Cancel</button>
            <button className="btn-secondary" onClick={generate} disabled={busy}>
              {generating ? <Spinner className="h-4 w-4" /> : <RefreshCw className="h-4 w-4" />} Regenerate
            </button>
            <button className="btn-primary" onClick={save} disabled={busy || !hasTasks}>
              {saving && <Spinner className="h-4 w-4 text-white" />} Save plan
            </button>
          </>
        ) : (
          <>
            <button className="btn-secondary" onClick={close} disabled={busy}>Cancel</button>
            <button className="btn-primary" type="submit" form="generate-form" disabled={busy}>
              {generating ? <Spinner className="h-4 w-4 text-white" /> : <Sparkles className="h-4 w-4" />}
              {generating ? 'Generating…' : 'Generate'}
            </button>
          </>
        )
      }
    >
      {generating && !preview && (
        <div className="flex flex-col items-center gap-3 py-10 text-center">
          <Spinner className="h-8 w-8" />
          <p className="text-sm text-slate-600">Building your personalised plan… this can take a few seconds.</p>
        </div>
      )}
      {!generating && !preview && (
        <form id="generate-form" onSubmit={generate} className="space-y-4">
          <p className="text-sm text-slate-600">
            The AI uses your subjects, pending topics, upcoming exams, weak subjects and study settings. You can review
            the plan before anything is saved.
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="plan-start">From</label>
              <input id="plan-start" type="date" required className="input" value={range.start_date}
                onChange={(e) => setRange({ ...range, start_date: e.target.value })} />
            </div>
            <div>
              <label className="label" htmlFor="plan-end">To</label>
              <input id="plan-end" type="date" required min={range.start_date} className="input" value={range.end_date}
                onChange={(e) => setRange({ ...range, end_date: e.target.value })} />
            </div>
          </div>
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
        </form>
      )}
      {preview && (
        <div className={generating ? 'pointer-events-none opacity-50' : ''}>
          {error && <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
          <Preview preview={preview} />
        </div>
      )}
    </Modal>
  )
}
