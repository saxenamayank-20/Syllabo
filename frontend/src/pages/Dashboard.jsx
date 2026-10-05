import { Link } from 'react-router-dom'
import {
  ArrowRight, ArrowUp, BarChart3, CalendarClock, ChevronRight, ClipboardCheck, ClipboardList, Lightbulb,
  PartyPopper, Target, TrendingDown, Trophy,
} from 'lucide-react'
import { useApi } from '../api/useApi'
import { useTaskToggle } from '../api/tasks'
import PerformanceChart, { ChartLegend } from '../components/PerformanceChart'
import TaskItem from '../components/TaskItem'
import { CardHeader, EmptyState, LoadingBlock } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { formatLongDate, greeting, parseISODate, toISODate } from '../utils/date'

const TONES = {
  green: 'bg-emerald-50 text-emerald-600',
  red: 'bg-red-50 text-red-500',
  blue: 'bg-primary-50 text-primary-600',
  amber: 'bg-amber-50 text-amber-500',
}

function StatCard({ icon: Icon, tone, value, label, sub, subClass = 'text-emerald-600' }) {
  return (
    <div className="card flex flex-col items-start gap-3 p-4 sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl sm:h-14 sm:w-14 ${TONES[tone]}`}>
        <Icon className="h-6 w-6 sm:h-7 sm:w-7" />
      </div>
      <div className="w-full min-w-0">
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-600">{label}</p>
        {sub && <p className={`mt-1 truncate text-xs font-medium ${subClass}`}>{sub}</p>}
      </div>
    </div>
  )
}

function ViewAll({ to, label = 'View All' }) {
  return (
    <Link to={to} className="flex items-center gap-1 text-xs font-medium text-primary-600 hover:underline">
      {label} <ArrowRight className="h-3.5 w-3.5" />
    </Link>
  )
}

function StatCards({ summary }) {
  const s = summary
  const progressUp = s.progress_change_this_week > 0
  const gradeGood = s.current_grade === 'A' || s.current_grade === 'B'
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
      <StatCard
        icon={ClipboardCheck} tone="green" value={s.today_tasks_total} label="Today's Tasks"
        sub={`${s.today_tasks_completed} completed`}
      />
      <StatCard
        icon={Target} tone="red" value={s.days_to_next_exam ?? '—'} label="Days to Exam"
        sub={s.next_exam ? s.next_exam.title : 'No upcoming exams'}
        subClass={s.next_exam ? 'text-primary-600' : 'text-slate-400'}
      />
      <StatCard
        icon={BarChart3} tone="blue" value={`${Math.round(s.overall_progress)}%`} label="Overall Progress"
        sub={
          <span className="inline-flex items-center gap-1">
            {progressUp && <ArrowUp className="h-3 w-3" />}+{s.progress_change_this_week}% this week
          </span>
        }
        subClass={progressUp ? 'text-emerald-600' : 'text-slate-400'}
      />
      <StatCard
        icon={Trophy} tone="amber" value={s.current_grade ?? '—'} label="Current Grade"
        sub={s.current_grade ? (gradeGood ? 'Great work!' : 'Keep pushing!') : 'No marks yet'}
        subClass={s.current_grade ? (gradeGood ? 'text-emerald-600' : 'text-amber-600') : 'text-slate-400'}
      />
    </div>
  )
}

function UpcomingExams({ exams, loading }) {
  return (
    <div className="card p-5">
      <CardHeader title="Upcoming Exams" action={<ViewAll to="/subjects#exams" />} />
      {loading ? (
        <LoadingBlock />
      ) : !exams?.length ? (
        <EmptyState icon={CalendarClock} title="No exams added yet" hint="Add exams from the Subjects page." />
      ) : (
        <ul className="divide-y divide-slate-100">
          {exams.slice(0, 3).map((exam) => {
            const d = parseISODate(exam.exam_date)
            return (
              <li key={exam.id} className="flex items-center gap-4 py-3">
                <div className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-xl bg-red-50 leading-none">
                  <span className="text-[10px] font-semibold uppercase text-red-500">
                    {d.toLocaleDateString('en-GB', { month: 'short' })}
                  </span>
                  <span className="mt-0.5 text-lg font-bold text-slate-900">{String(d.getDate()).padStart(2, '0')}</span>
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-800">{exam.title}</p>
                  <p className="truncate text-xs text-slate-500">{exam.syllabus || 'No syllabus added'}</p>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

function Recommendations({ summary }) {
  const weak = summary.weak_subjects
  const hasMarks = summary.subject_performance.some((p) => p.avg_percentage != null)
  return (
    <div className="card p-5">
      <CardHeader title="AI Recommendations" icon={Lightbulb} />
      {!hasMarks ? (
        <EmptyState icon={Lightbulb} title="No recommendations yet" hint="Add some marks to get suggestions." />
      ) : !weak.length ? (
        <EmptyState icon={PartyPopper} title="All subjects are on target" hint="Keep up the consistent work!" />
      ) : (
        <ul className="space-y-3">
          {weak.map((s) => (
            <li key={s.subject_id}>
              <Link
                to="/performance"
                className="flex items-center gap-3 rounded-xl bg-emerald-50/70 p-3 transition hover:bg-emerald-50"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-emerald-600">
                  <TrendingDown className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-800">Focus more on {s.subject}</p>
                  <p className="text-xs text-slate-500">
                    Your average ({s.avg_percentage}%) is below your target ({s.target_score}%).
                  </p>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const today = toISODate()
  const summary = useApi('/dashboard/summary')
  const tasks = useApi(`/tasks?date=${today}`, [])
  const exams = useApi('/exams?upcoming=true', [])
  const { toggle, busyId } = useTaskToggle(tasks.setData, () => summary.reload({ silent: true }))

  const firstName = user.name.split(' ')[0]

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
            {greeting()}, {firstName}! <span aria-hidden>👋</span>
          </h1>
          <p className="mt-1 text-sm text-slate-500">Stay consistent, keep learning, and make it happen.</p>
        </div>
        <p className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <CalendarClock className="h-4 w-4 text-slate-500" /> {formatLongDate()}
        </p>
      </div>

      {summary.loading && !summary.data ? (
        <div className="card"><LoadingBlock /></div>
      ) : summary.data ? (
        <StatCards summary={summary.data} />
      ) : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-5">
          <CardHeader title="Today's Study Plan" action={<ViewAll to="/study-plan" />} />
          {tasks.loading ? (
            <LoadingBlock />
          ) : !tasks.data.length ? (
            <EmptyState
              icon={ClipboardList}
              title="No tasks scheduled for today"
              action={<Link to="/study-plan" className="btn-secondary">Add a task</Link>}
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {tasks.data.map((t) => (
                <TaskItem key={t.id} task={t} busy={busyId === t.id} onToggle={toggle} />
              ))}
            </ul>
          )}
        </div>

        <div className="card p-5">
          <CardHeader title="Performance Overview" action={<ChartLegend />} />
          {summary.loading && !summary.data ? (
            <LoadingBlock />
          ) : (
            <PerformanceChart data={summary.data?.subject_performance} height={290} />
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <UpcomingExams exams={exams.data} loading={exams.loading} />
        {summary.data && <Recommendations summary={summary.data} />}
      </div>
    </div>
  )
}
