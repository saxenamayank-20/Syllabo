import { Sparkles } from 'lucide-react'

export default function ComingSoon({ title, icon: Icon = Sparkles }) {
  return (
    <div className="card flex min-h-[60vh] flex-col items-center justify-center p-8 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-50 text-primary-600">
        <Icon className="h-7 w-7" />
      </div>
      <h1 className="text-xl font-bold text-slate-900">{title}</h1>
      <p className="mt-2 max-w-sm text-sm text-slate-500">This section is coming soon. We&apos;re working on it!</p>
    </div>
  )
}
