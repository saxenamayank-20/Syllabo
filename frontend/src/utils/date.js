// Dates are shown in the logged-in user's timezone (saved on their profile) so that "today"
// matches what the backend uses. AuthContext calls setActiveTimeZone() whenever the user loads.
let activeTimeZone = browserTimeZone()

export function browserTimeZone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}

export function setActiveTimeZone(zone) {
  activeTimeZone = zone || browserTimeZone()
}

/** YYYY-MM-DD for `date` (default: now) in the active timezone. */
export function toISODate(date = new Date()) {
  // en-CA formats as YYYY-MM-DD
  return new Intl.DateTimeFormat('en-CA', { timeZone: activeTimeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(date)
}

/** YYYY-MM-DD that is `days` after today in the active timezone. */
export function addDaysISO(days, from = toISODate()) {
  const d = parseISODate(from)
  d.setDate(d.getDate() + days)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** Parse YYYY-MM-DD as a calendar date (local midnight) for display. */
export function parseISODate(value) {
  const [y, m, d] = value.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function formatLongDate(date = new Date()) {
  return date.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', timeZone: activeTimeZone })
}

export function formatDate(value) {
  return parseISODate(value).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDayHeading(value) {
  const label = parseISODate(value).toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short' })
  if (value === toISODate()) return `Today · ${label}`
  if (value === addDaysISO(1)) return `Tomorrow · ${label}`
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
  const h = Number(new Intl.DateTimeFormat('en-GB', { hour: 'numeric', hourCycle: 'h23', timeZone: activeTimeZone }).format(date))
  if (h < 12) return 'Good Morning'
  if (h < 17) return 'Good Afternoon'
  return 'Good Evening'
}
