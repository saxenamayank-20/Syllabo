import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { BookOpen, CalendarClock, Pencil, Plus, Trash2 } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import { useApi } from '../api/useApi'
import { CardHeader, Checkbox, ConfirmDialog, EmptyState, LoadingBlock, Modal, PageHeader, Spinner, SubjectDot } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { formatDate, toISODate } from '../utils/date'

const COLORS = ['#2563eb', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#0ea5e9', '#64748b']

function SubjectModal({ open, subject, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({ name: '', color: COLORS[0], target_score: 75 })
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) setForm(subject ? { name: subject.name, color: subject.color, target_score: subject.target_score } : { name: '', color: COLORS[0], target_score: 75 })
  }, [open, subject])

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const payload = { ...form, target_score: Number(form.target_score) }
      if (subject) await api.patch(`/subjects/${subject.id}`, payload)
      else await api.post('/subjects', payload)
      toast.success(subject ? 'Subject updated' : 'Subject added')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      title={subject ? 'Edit subject' : 'Add subject'}
      onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" onClick={onClose} type="button">Cancel</button>
          <button className="btn-primary" form="subject-form" type="submit" disabled={busy}>
            {busy && <Spinner className="h-4 w-4 text-white" />} Save
          </button>
        </>
      }
    >
      <form id="subject-form" onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="subject-name">Name</label>
          <input id="subject-name" className="input" required maxLength={120} value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <label className="label" htmlFor="subject-target">Target score (%)</label>
          <input id="subject-target" type="number" min={0} max={100} required className="input" value={form.target_score}
            onChange={(e) => setForm({ ...form, target_score: e.target.value })} />
        </div>
        <div>
          <span className="label">Color</span>
          <div className="flex flex-wrap gap-2">
            {COLORS.map((c) => (
              <button key={c} type="button" onClick={() => setForm({ ...form, color: c })}
                className={`h-8 w-8 rounded-full ring-offset-2 transition ${form.color === c ? 'ring-2 ring-slate-400' : ''}`}
                style={{ backgroundColor: c }} aria-label={`Color ${c}`} aria-pressed={form.color === c} />
            ))}
          </div>
        </div>
      </form>
    </Modal>
  )
}

function SubjectCard({ subject, onEdit, onDelete, onChanged }) {
  const toast = useToast()
  const [topicName, setTopicName] = useState('')
  const [adding, setAdding] = useState(false)
  const [busyTopic, setBusyTopic] = useState(null)

  const total = subject.topics.length
  const done = subject.topics.filter((t) => t.status === 'completed').length
  const pct = total ? Math.round((done / total) * 100) : 0

  const addTopic = async (e) => {
    e.preventDefault()
    if (!topicName.trim()) return
    setAdding(true)
    try {
      await api.post(`/subjects/${subject.id}/topics`, { name: topicName.trim() })
      setTopicName('')
      await onChanged()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setAdding(false)
    }
  }

  const run = async (topicId, fn) => {
    setBusyTopic(topicId)
    try {
      await fn()
      await onChanged()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusyTopic(null)
    }
  }

  return (
    <div className="card flex flex-col p-5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="flex items-center gap-2 font-semibold text-slate-900">
            <SubjectDot color={subject.color} /> <span className="truncate">{subject.name}</span>
          </h3>
          <p className="mt-1 text-xs text-slate-500">Target {subject.target_score}% · {done}/{total} topics done</p>
        </div>
        <div className="flex shrink-0">
          <button className="btn-ghost" onClick={() => onEdit(subject)} aria-label={`Edit ${subject.name}`}><Pencil className="h-4 w-4" /></button>
          <button className="btn-ghost hover:text-red-600" onClick={() => onDelete(subject)} aria-label={`Delete ${subject.name}`}><Trash2 className="h-4 w-4" /></button>
        </div>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: subject.color }} />
      </div>

      <ul className="mt-4 flex-1 space-y-1">
        {subject.topics.length === 0 && <li className="py-2 text-xs text-slate-400">No topics yet — add the first one below.</li>}
        {subject.topics.map((topic) => {
          const completed = topic.status === 'completed'
          return (
            <li key={topic.id} className="group flex items-center gap-3 rounded-lg px-1 py-1.5 hover:bg-slate-50">
              <Checkbox checked={completed} disabled={busyTopic === topic.id} label={`Toggle ${topic.name}`}
                onChange={() => run(topic.id, () => api.patch(`/topics/${topic.id}`))} />
              <span className={`flex-1 text-sm ${completed ? 'text-slate-400 line-through' : 'text-slate-700'}`}>{topic.name}</span>
              <button className="btn-ghost p-1 opacity-100 hover:text-red-600 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100"
                aria-label={`Delete topic ${topic.name}`} onClick={() => run(topic.id, () => api.delete(`/topics/${topic.id}`))}>
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          )
        })}
      </ul>

      <form onSubmit={addTopic} className="mt-3 flex gap-2">
        <input className="input" placeholder="Add a topic…" value={topicName} maxLength={200}
          onChange={(e) => setTopicName(e.target.value)} aria-label={`New topic for ${subject.name}`} />
        <button className="btn-secondary px-3" disabled={adding || !topicName.trim()} aria-label="Add topic">
          {adding ? <Spinner className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        </button>
      </form>
    </div>
  )
}

const emptyExam = () => ({ title: '', subject_id: '', exam_date: toISODate(), syllabus: '' })

const examToForm = (e) => ({
  title: e.title,
  subject_id: e.subject_id ? String(e.subject_id) : '',
  exam_date: e.exam_date,
  syllabus: e.syllabus,
})

/** Add an exam, or edit `exam` when given. */
function ExamModal({ open, exam, subjects, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState(emptyExam)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) setForm(exam ? examToForm(exam) : emptyExam())
  }, [open, exam])

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const payload = { ...form, subject_id: form.subject_id ? Number(form.subject_id) : null }
      if (exam) await api.patch(`/exams/${exam.id}`, payload)
      else await api.post('/exams', payload)
      toast.success(exam ? 'Exam updated' : 'Exam added')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  return (
    <Modal open={open} title={exam ? 'Edit exam' : 'Add exam'} onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" type="button" onClick={onClose}>Cancel</button>
          <button className="btn-primary" type="submit" form="exam-form" disabled={busy}>
            {busy && <Spinner className="h-4 w-4 text-white" />} Save
          </button>
        </>
      }
    >
      <form id="exam-form" onSubmit={submit} className="space-y-4">
        <div>
          <label className="label" htmlFor="exam-title">Title</label>
          <input id="exam-title" className="input" required maxLength={200} value={form.title} onChange={set('title')} placeholder="e.g. Mathematics - Unit Test" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="exam-subject">Subject</label>
            <select id="exam-subject" className="input" value={form.subject_id} onChange={set('subject_id')}>
              <option value="">General</option>
              {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="exam-date">Date</label>
            <input id="exam-date" type="date" className="input" required value={form.exam_date} onChange={set('exam_date')} />
          </div>
        </div>
        <div>
          <label className="label" htmlFor="exam-syllabus">Syllabus</label>
          <textarea id="exam-syllabus" className="input" rows={3} value={form.syllabus} onChange={set('syllabus')} placeholder="e.g. Chapters 1 - 5" />
        </div>
      </form>
    </Modal>
  )
}

function ExamsSection({ subjects }) {
  const toast = useToast()
  const exams = useApi('/exams', [])
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)
  const today = toISODate()
  const byId = Object.fromEntries(subjects.map((s) => [s.id, s]))

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await api.delete(`/exams/${deleting.id}`)
      toast.success('Exam deleted')
      setDeleting(null)
      exams.reload({ silent: true })
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section id="exams" className="card scroll-mt-24 p-5">
      <CardHeader title="Exams" icon={CalendarClock}
        action={<button className="btn-primary" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add exam</button>} />
      {exams.loading ? (
        <LoadingBlock />
      ) : !exams.data.length ? (
        <EmptyState icon={CalendarClock} title="No exams added yet" hint="Add your upcoming exams to track the countdown." />
      ) : (
        <ul className="divide-y divide-slate-100">
          {exams.data.map((exam) => {
            const past = exam.exam_date < today
            const subject = byId[exam.subject_id]
            return (
              <li key={exam.id} className={`flex items-center gap-4 py-3 ${past ? 'opacity-60' : ''}`}>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-800">{exam.title}</p>
                  <p className="mt-0.5 flex items-center gap-1.5 truncate text-xs text-slate-500">
                    {subject && <><SubjectDot color={subject.color} /> {subject.name} ·{' '}</>}
                    {exam.syllabus || 'No syllabus'}
                  </p>
                </div>
                <span className={`shrink-0 text-xs font-medium ${past ? 'text-slate-400' : 'text-slate-700'}`}>
                  {formatDate(exam.exam_date)}{past && ' (past)'}
                </span>
                <button className="btn-ghost" onClick={() => setEditing(exam)} aria-label={`Edit ${exam.title}`}>
                  <Pencil className="h-4 w-4" />
                </button>
                <button className="btn-ghost -ml-2 hover:text-red-600" onClick={() => setDeleting(exam)} aria-label={`Delete ${exam.title}`}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            )
          })}
        </ul>
      )}
      <ExamModal open={adding || Boolean(editing)} exam={editing} subjects={subjects}
        onClose={() => { setAdding(false); setEditing(null) }} onSaved={() => exams.reload({ silent: true })} />
      <ConfirmDialog open={Boolean(deleting)} title="Delete exam" busy={busy} onClose={() => setDeleting(null)} onConfirm={confirmDelete}
        message={`Delete "${deleting?.title}"? This cannot be undone.`} />
    </section>
  )
}

export default function Subjects() {
  const toast = useToast()
  const location = useLocation()
  const subjects = useApi('/subjects', [])
  const [editing, setEditing] = useState(null) // null = closed, {} = new, subject = edit
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (location.hash === '#exams' && !subjects.loading) {
      document.getElementById('exams')?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [location.hash, subjects.loading])

  const reload = () => subjects.reload({ silent: true })

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await api.delete(`/subjects/${deleting.id}`)
      toast.success('Subject deleted')
      setDeleting(null)
      reload()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Subjects" subtitle="Manage your subjects, topics and exams."
        action={<button className="btn-primary" onClick={() => setEditing({})}><Plus className="h-4 w-4" /> Add subject</button>} />

      {subjects.loading ? (
        <div className="card"><LoadingBlock /></div>
      ) : !subjects.data.length ? (
        <div className="card">
          <EmptyState icon={BookOpen} title="No subjects added yet" hint="Start by adding the subjects you are studying."
            action={<button className="btn-primary" onClick={() => setEditing({})}><Plus className="h-4 w-4" /> Add subject</button>} />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
          {subjects.data.map((s) => (
            <SubjectCard key={s.id} subject={s} onEdit={setEditing} onDelete={setDeleting} onChanged={reload} />
          ))}
        </div>
      )}

      {!subjects.loading && <ExamsSection subjects={subjects.data} />}

      <SubjectModal open={editing !== null} subject={editing?.id ? editing : null} onClose={() => setEditing(null)} onSaved={reload} />
      <ConfirmDialog open={Boolean(deleting)} title="Delete subject" busy={busy} onClose={() => setDeleting(null)} onConfirm={confirmDelete}
        message={`Delete "${deleting?.name}"? Its topics, tasks and marks will also be deleted.`} />
    </div>
  )
}
