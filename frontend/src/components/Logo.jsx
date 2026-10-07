import { GraduationCap } from 'lucide-react'

export default function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <GraduationCap className="h-9 w-9 text-slate-900" strokeWidth={2} />
      <div className="leading-tight">
        <p className="text-xl font-bold text-slate-900">
          Sylla<span className="text-primary-600 dark:text-primary-400">bo</span>
        </p>
        <p className="text-[11px] text-slate-500">Plan • Learn • Grow</p>
      </div>
    </div>
  )
}
