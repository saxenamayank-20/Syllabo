import { useEffect, useMemo, useState } from 'react'
import { ClipboardList, Plus, Sparkles } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import { useApi } from '../api/useApi'
import { useTaskToggle } from '../api/tasks'
import GeneratePlanModal from '../components/GeneratePlanModal'
import PlanSettings from '../components/PlanSettings'
import TaskItem from '../components/TaskItem'
import { ConfirmDialog, EmptyState, LoadingBlock, Modal, PageHeader, Spinner } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { formatDayHeading, formatDuration, toISODate } from '../utils/date'

const emptyTask = () => ({ subject_id: '', topic_id: '', title: '', scheduled_date: toISODate(), start_time: '', duration_mins: 60 })

function TaskModal({ open, subjects, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState(emptyTask)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) setForm(emptyTask())
  }, [open])

  const topics = subjects.find((s) => s.id === Number(form.subject_id))?.topics ?? []
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.post('/tasks', {
        subject_id: Number(form.subject_id),
        topic_id: form.topic_id ? Number(form.topic_id) : null,
        title: form.title.trim(),
        scheduled_date: form.scheduled_date,
        start_time: form.start_time || null,
        duration_mins: Number(form.duration_mins),
      })
      toast.success('Task added')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={open} title="Add study task" onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" type="button" onClick={onClose}>Cancel</button>
          <button className="btn-primary" type="submit" form="task-form" disabled={busy || !subjects.length}>
            {busy && <Spinner className="h-4 w-4 text-white" />} Save
          </button>
        </>
      }
    >
      {!subjects.length ? (
        <EmptyState title="Add a subject first" hint="Every task belongs to a subject." className="py-4" />
      ) : (
        <form id="task-form" onSubmit={submit} className="space-y-4">
          <div>
            <label className="label" htmlFor="task-title">Title</label>
            <input id="task-title" className="input" required maxLength={200} placeholder="e.g. Revise Chapter 4" value={form.title} onChange={set('title')} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label" htmlFor="task-subject">Subject</label>
              <select id="task-subject" className="input" required value={form.subject_id}
                onChange={(e) => setForm({ ...form, subject_id: e.target.value, topic_id: '' })}>
                <option value="" disabled>Select</option>
                {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="task-topic">Topic (optional)</label>
              <select id="task-topic" className="input" value={form.topic_id} onChange={set('topic_id')} disabled={!topics.length}>
                <option value="">None</option>
                {topics.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div className="col-span-2 sm:col-span-1">
              <label className="label" htmlFor="task-date">Date</label>
              <input id="task-date" type="date" required className="input" value={form.scheduled_date} onChange={set('scheduled_date')} />
            </div>
            <div>
              <label className="label" htmlFor="task-time">Start time</label>
              <input id="task-time" type="time" className="input" value={form.start_time} onChange={set('start_time')} />
            </div>
            <div>
              <label className="label" htmlFor="task-duration">Minutes</label>
              <input id="task-duration" type="number" min={5} max={960} step={5} required className="input" value={form.duration_mins} onChange={set('duration_mins')} />
            </div>
          </div>
        </form>
      )}
    </Modal>
  )
}

export default function StudyPlan() {
  const toast = useToast()
  const tasks = useApi('/tasks', [])
  const subjects = useApi('/subjects', [])
  const [view, setView] = useState('upcoming')
  const [adding, setAdding] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)
  const { toggle, busyId } = useTaskToggle(tasks.setData)
  const today = toISODate()

  const groups = useMemo(() => {
    const visible = view === 'upcoming' ? tasks.data.filter((t) => t.scheduled_date >= today) : [...tasks.data].reverse()
    const map = new Map()
    for (const t of visible) {
      if (!map.has(t.scheduled_date)) map.set(t.scheduled_date, [])
      map.get(t.scheduled_date).push(t)
    }
    // Within a day keep chronological order even in the "past" (newest day first) view
    return [...map.entries()].map(([date, list]) => [date, view === 'upcoming' ? list : list.reverse()])
  }, [tasks.data, view, today])

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await api.delete(`/tasks/${deleting.id}`)
      tasks.setData((list) => list.filter((t) => t.id !== deleting.id))
      toast.success('Task deleted')
      setDeleting(null)
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="My Study Plan" subtitle="Your study tasks, grouped by day."
        action={
          <div className="flex flex-wrap gap-2">
            <button className="btn-secondary" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add task</button>
            <button className="btn-primary" onClick={() => setGenerating(true)}><Sparkles className="h-4 w-4" /> Generate AI Plan</button>
          </div>
        } />

      <PlanSettings />

      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm" role="tablist">
        {[['upcoming', 'Upcoming'], ['all', 'All tasks']].map(([key, label]) => (
          <button key={key} role="tab" aria-selected={view === key} onClick={() => setView(key)}
            className={`rounded-md px-3 py-1.5 font-medium transition ${view === key ? 'bg-primary-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}>
            {label}
          </button>
        ))}
      </div>

      {tasks.loading ? (
        <div className="card"><LoadingBlock /></div>
      ) : !groups.length ? (
        <div className="card">
          <EmptyState icon={ClipboardList} title={view === 'upcoming' ? 'No upcoming tasks' : 'No tasks added yet'}
            hint="Add a task to start planning your study days."
            action={<button className="btn-primary" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add task</button>} />
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map(([date, list]) => {
            const done = list.filter((t) => t.status === 'completed').length
            const minutes = list.reduce((sum, t) => sum + t.duration_mins, 0)
            return (
              <section key={date} className="card p-5">
                <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
                  <h2 className={`font-semibold ${date === today ? 'text-primary-700' : 'text-slate-900'}`}>{formatDayHeading(date)}</h2>
                  <p className="text-xs text-slate-500">{done}/{list.length} done · {formatDuration(minutes)}</p>
                </div>
                <ul className="divide-y divide-slate-100">
                  {list.map((t) => (
                    <TaskItem key={t.id} task={t} busy={busyId === t.id} onToggle={toggle} onDelete={setDeleting} />
                  ))}
                </ul>
              </section>
            )
          })}
        </div>
      )}

      <TaskModal open={adding} subjects={subjects.data} onClose={() => setAdding(false)} onSaved={() => tasks.reload({ silent: true })} />
      <GeneratePlanModal open={generating} onClose={() => setGenerating(false)} onSaved={() => tasks.reload({ silent: true })} />
      <ConfirmDialog open={Boolean(deleting)} title="Delete task" busy={busy} onClose={() => setDeleting(null)} onConfirm={confirmDelete}
        message={`Delete "${deleting?.title}"?`} />
    </div>
  )
}
