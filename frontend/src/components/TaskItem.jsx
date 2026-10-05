import { Sparkles, Trash2 } from 'lucide-react'
import { formatDuration, formatTime } from '../utils/date'
import { Checkbox } from './ui'

export default function TaskItem({ task, busy, onToggle, onDelete }) {
  const done = task.status === 'completed'
  return (
    <li className="group flex items-center gap-4 py-3">
      <Checkbox checked={done} disabled={busy} onChange={() => onToggle(task)} label={`Mark "${task.title}" ${done ? 'pending' : 'complete'}`} />
      <div className="min-w-0 flex-1">
        <p className={`truncate text-sm font-medium ${done ? 'text-slate-400 line-through' : 'text-slate-800'}`}>{task.title}</p>
        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500">
          <span>{task.subject_name}</span>
          <span aria-hidden>•</span>
          <span>{formatDuration(task.duration_mins)}</span>
          {task.source === 'ai' && (
            <span className="ml-1 inline-flex items-center gap-0.5 rounded bg-violet-50 px-1.5 py-0.5 text-[10px] font-medium text-violet-700">
              <Sparkles className="h-3 w-3" /> AI
            </span>
          )}
        </p>
      </div>
      {task.start_time && <span className="shrink-0 text-xs text-slate-400">{formatTime(task.start_time)}</span>}
      {onDelete && (
        <button
          onClick={() => onDelete(task)}
          className="btn-ghost opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100"
          aria-label={`Delete "${task.title}"`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}
    </li>
  )
}
