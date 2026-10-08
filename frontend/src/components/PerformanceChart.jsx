import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BarChart3 } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { EmptyState } from './ui'

// chart colours per theme (checked for contrast and colour blindness)
const CHART_COLORS = {
  light: { marks: '#2563eb', target: '#d97706', grid: '#eef2f7', axis: '#e2e8f0', tick: '#475569', tickMuted: '#64748b', label: '#334155', cursor: '#f1f5f9' },
  dark: { marks: '#3b82f6', target: '#d97706', grid: '#1e293b', axis: '#2b3750', tick: '#aab6c8', tickMuted: '#94a3b8', label: '#c6cfdc', cursor: '#172036' },
}

function useChartColors() {
  return CHART_COLORS[useTheme().theme]
}

function ChartTooltip({ active, payload, label, colors }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="rounded-lg border border-slate-200 bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-semibold text-slate-900">{label}</p>
      <p className="flex items-center gap-2 text-slate-600">
        <span className="h-2 w-2 rounded-sm" style={{ background: colors.marks }} />
        Marks: <span className="font-medium text-slate-900">{row.marks == null ? 'No marks yet' : `${row.marks}%`}</span>
      </p>
      <p className="flex items-center gap-2 text-slate-600">
        <span className="h-2 w-2 rounded-sm" style={{ background: colors.target }} />
        Target: <span className="font-medium text-slate-900">{row.target}%</span>
      </p>
    </div>
  )
}

export function ChartLegend() {
  const colors = useChartColors()
  return (
    <div className="flex items-center gap-4 text-xs text-slate-600">
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full" style={{ background: colors.marks }} /> Marks
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full" style={{ background: colors.target }} /> Target
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

// marks vs target bars per subject
export default function PerformanceChart({ data, height = 260 }) {
  const narrow = useIsNarrow()
  const colors = useChartColors()
  if (!data?.length) {
    return <EmptyState icon={BarChart3} title="No subjects yet" hint="Add subjects and marks to see your performance." />
  }
  const rows = data.map((s) => ({ name: s.subject, marks: s.avg_percentage, target: s.target_score }))

  return (
    <div style={{ height }} role="img" aria-label="Bar chart of average marks versus target per subject">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 20, right: 4, left: -20, bottom: 0 }} barGap={2} barCategoryGap="28%">
          <CartesianGrid vertical={false} stroke={colors.grid} />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={{ stroke: colors.axis }}
            tick={{ fontSize: 12, fill: colors.tick }}
            interval={0}
            // shorten names on phones, tooltip has the full one
            tickFormatter={(name) => (narrow && name.length > 5 ? `${name.slice(0, 4)}.` : name)}
          />
          <YAxis domain={[0, 100]} ticks={[0, 20, 40, 60, 80, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: colors.tickMuted }} />
          <Tooltip content={<ChartTooltip colors={colors} />} cursor={{ fill: colors.cursor }} />
          <Bar dataKey="marks" name="Marks" fill={colors.marks} radius={[4, 4, 0, 0]} maxBarSize={28} isAnimationActive={false}>
            <LabelList dataKey="marks" position="top" formatter={(v) => (v == null ? '' : `${Math.round(v)}%`)} fontSize={11} fill={colors.label} />
          </Bar>
          <Bar dataKey="target" name="Target" fill={colors.target} radius={[4, 4, 0, 0]} maxBarSize={28} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
