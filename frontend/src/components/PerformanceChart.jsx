import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BarChart3 } from 'lucide-react'
import { EmptyState } from './ui'

// Validated pair (dataviz palette check): blue marks vs amber target.
const MARKS_COLOR = '#2563eb'
const TARGET_COLOR = '#d97706'

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-semibold text-slate-900">{label}</p>
      <p className="flex items-center gap-2 text-slate-600">
        <span className="h-2 w-2 rounded-sm" style={{ background: MARKS_COLOR }} />
        Marks: <span className="font-medium text-slate-900">{row.marks == null ? 'No marks yet' : `${row.marks}%`}</span>
      </p>
      <p className="flex items-center gap-2 text-slate-600">
        <span className="h-2 w-2 rounded-sm" style={{ background: TARGET_COLOR }} />
        Target: <span className="font-medium text-slate-900">{row.target}%</span>
      </p>
    </div>
  )
}

export function ChartLegend() {
  return (
    <div className="flex items-center gap-4 text-xs text-slate-600">
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full" style={{ background: MARKS_COLOR }} /> Marks
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full" style={{ background: TARGET_COLOR }} /> Target
      </span>
    </div>
  )
}

function useIsNarrow(query = '(max-width: 640px)') {
  const [narrow, setNarrow] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const mq = window.matchMedia(query)
    const onChange = (e) => setNarrow(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [query])
  return narrow
}

/** Grouped bars: average mark % vs target % per subject. `data` is dashboard subject_performance. */
export default function PerformanceChart({ data, height = 260 }) {
  const narrow = useIsNarrow()
  if (!data?.length) {
    return <EmptyState icon={BarChart3} title="No subjects yet" hint="Add subjects and marks to see your performance." />
  }
  const rows = data.map((s) => ({ name: s.subject, marks: s.avg_percentage, target: s.target_score }))

  return (
    <div style={{ height }} role="img" aria-label="Bar chart of average marks versus target per subject">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 20, right: 4, left: -20, bottom: 0 }} barGap={2} barCategoryGap="28%">
          <CartesianGrid vertical={false} stroke="#eef2f7" />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            tick={{ fontSize: 12, fill: '#475569' }}
            interval={0}
            // Subject names collide on phones; abbreviate there (the tooltip shows the full name).
            tickFormatter={(name) => (narrow && name.length > 5 ? `${name.slice(0, 4)}.` : name)}
          />
          <YAxis domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: '#f1f5f9' }} />
          <Bar dataKey="marks" name="Marks" fill={MARKS_COLOR} radius={[4, 4, 0, 0]} maxBarSize={28} isAnimationActive={false}>
            <LabelList dataKey="marks" position="top" formatter={(v) => (v == null ? '' : `${Math.round(v)}%`)} fontSize={11} fill="#334155" />
          </Bar>
          <Bar dataKey="target" name="Target" fill={TARGET_COLOR} radius={[4, 4, 0, 0]} maxBarSize={28} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
