/** YYYY-MM-DD in the user's local timezone (toISOString would shift to UTC). */
export function toISODate(date = new Date()) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** Parse YYYY-MM-DD as a local date. */
export function parseISODate(value) {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function formatLongDate(date = new Date()) {
  return date.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDate(value) {
  return parseISODate(value).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDayHeading(value) {
  const date = parseISODate(value)
  const today = toISODate()
  const tomorrow = toISODate(new Date(Date.now() + 86_400_000))
  const label = date.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short' })
  if (value === today) return `Today · ${label}`
  if (value === tomorrow) return `Tomorrow · ${label}`
  return label
}

/** "14:00:00" -> "2:00 PM" */
export function formatTime(value) {
  if (!value) return ''
  const [h, m] = value.split(':').map(Number)
  const suffix = h >= 12 ? 'PM' : 'AM'
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${suffix}`
}

export function formatDuration(mins) {
  if (mins < 60) return `${mins} mins`
  const h = Math.floor(mins / 60)
  const rest = mins % 60
  return rest ? `${h}h ${rest}m` : `${h} hour${h > 1 ? 's' : ''}`
}

export function greeting(date = new Date()) {
  const h = date.getHours()
  if (h < 12) return 'Good Morning'
  if (h < 17) return 'Good Afternoon'
  return 'Good Evening'
}
