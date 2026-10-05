import { useState } from 'react'
import { BarChart3, ClipboardList, Pencil, Plus, Save, Trash2 } from 'lucide-react'
import api, { errorMessage } from '../api/client'
import { useApi } from '../api/useApi'
import PerformanceChart, { ChartLegend } from '../components/PerformanceChart'
import { CardHeader, ConfirmDialog, EmptyState, LoadingBlock, Modal, PageHeader, Spinner, SubjectDot } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { formatDate, toISODate } from '../utils/date'

const emptyMark = () => ({ subject_id: '', assessment_name: '', score: '', max_score: '100', assessment_date: toISODate() })

const markToForm = (m) => ({
  subject_id: String(m.subject_id),
  assessment_name: m.assessment_name,
  score: String(m.score),
  max_score: String(m.max_score),
  assessment_date: m.assessment_date,
})

/** Add a mark, or edit `mark` when given. */
function MarkForm({ subjects, mark, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState(() => (mark ? markToForm(mark) : emptyMark()))
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const payload = {
        ...form,
        subject_id: Number(form.subject_id),
        score: Number(form.score),
        max_score: Number(form.max_score),
      }
      if (mark) {
        await api.patch(`/marks/${mark.id}`, payload)
        toast.success('Mark updated')
      } else {
        await api.post('/marks', payload)
        toast.success('Mark added')
        setForm({ ...emptyMark(), subject_id: form.subject_id })
      }
      onSaved()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (!subjects.length) {
    return <EmptyState icon={Plus} title="Add a subject first" hint="Marks are recorded per subject." />
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label className="label" htmlFor="mark-subject">Subject</label>
        <select id="mark-subject" className="input" required value={form.subject_id} onChange={set('subject_id')}>
          <option value="" disabled>Select a subject</option>
          {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>
      <div>
        <label className="label" htmlFor="mark-name">Assessment</label>
        <input id="mark-name" className="input" required maxLength={200} placeholder="e.g. Unit Test 2" value={form.assessment_name} onChange={set('assessment_name')} />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label" htmlFor="mark-score">Score</label>
          <input id="mark-score" type="number" step="any" min={0} required className="input" value={form.score} onChange={set('score')} />
        </div>
        <div>
          <label className="label" htmlFor="mark-max">Out of</label>
          <input id="mark-max" type="number" step="any" min={0.01} required className="input" value={form.max_score} onChange={set('max_score')} />
        </div>
      </div>
      <div>
        <label className="label" htmlFor="mark-date">Date</label>
        <input id="mark-date" type="date" required className="input" value={form.assessment_date} onChange={set('assessment_date')} />
      </div>
      <button type="submit" className="btn-primary w-full" disabled={busy}>
        {busy ? <Spinner className="h-4 w-4 text-white" /> : mark ? <Save className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
        {mark ? 'Save changes' : 'Add mark'}
      </button>
    </form>
  )
}

export default function Performance() {
  const toast = useToast()
  const summary = useApi('/dashboard/summary')
  const subjects = useApi('/subjects', [])
  const marks = useApi('/marks', [])
  const [deleting, setDeleting] = useState(null)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(false)
  const colorById = Object.fromEntries(subjects.data.map((s) => [s.id, s.color]))

  const refresh = () => {
    marks.reload({ silent: true })
    summary.reload({ silent: true })
  }

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await api.delete(`/marks/${deleting.id}`)
      toast.success('Mark deleted')
      setDeleting(null)
      refresh()
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Performance" subtitle="Record your marks and compare them against your targets." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <CardHeader title="Performance Overview" action={<ChartLegend />} />
          {summary.loading && !summary.data ? <LoadingBlock /> : <PerformanceChart data={summary.data?.subject_performance} height={300} />}
        </div>
        <div className="card p-5">
          <CardHeader title="Add marks" />
          {subjects.loading ? <LoadingBlock /> : <MarkForm subjects={subjects.data} onSaved={refresh} />}
        </div>
      </div>

      <div className="card p-5">
        <CardHeader title="Past marks" icon={ClipboardList} />
        {marks.loading ? (
          <LoadingBlock />
        ) : !marks.data.length ? (
          <EmptyState icon={BarChart3} title="No marks added yet" hint="Use the form above to record your first assessment." />
        ) : (
          <div className="-mx-5 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-2 font-medium">Date</th>
                  <th className="px-5 py-2 font-medium">Subject</th>
                  <th className="px-5 py-2 font-medium">Assessment</th>
                  <th className="px-5 py-2 text-right font-medium">Score</th>
                  <th className="px-5 py-2 text-right font-medium">%</th>
                  <th className="px-5 py-2"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {marks.data.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-5 py-2.5 text-slate-600">{formatDate(m.assessment_date)}</td>
                    <td className="px-5 py-2.5">
                      <span className="flex items-center gap-2 text-slate-800"><SubjectDot color={colorById[m.subject_id] ?? '#94a3b8'} />{m.subject_name}</span>
                    </td>
                    <td className="px-5 py-2.5 text-slate-700">{m.assessment_name}</td>
                    <td className="whitespace-nowrap px-5 py-2.5 text-right tabular-nums text-slate-700">{m.score} / {m.max_score}</td>
                    <td className="px-5 py-2.5 text-right font-medium tabular-nums text-slate-900">{m.percentage}%</td>
                    <td className="whitespace-nowrap px-5 py-2.5 text-right">
                      <button className="btn-ghost" onClick={() => setEditing(m)} aria-label={`Edit ${m.assessment_name}`}>
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button className="btn-ghost hover:text-red-600" onClick={() => setDeleting(m)} aria-label={`Delete ${m.assessment_name}`}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={Boolean(editing)} title="Edit mark" onClose={() => setEditing(null)}>
        {editing && (
          <MarkForm key={editing.id} subjects={subjects.data} mark={editing}
            onSaved={() => { setEditing(null); refresh() }} />
        )}
      </Modal>
      <ConfirmDialog open={Boolean(deleting)} title="Delete mark" busy={busy} onClose={() => setDeleting(null)} onConfirm={confirmDelete}
        message={`Delete "${deleting?.assessment_name}" (${deleting?.subject_name})?`} />
    </div>
  )
}
