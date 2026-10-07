import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function ThemeToggle({ className = '' }) {
  const { isDark, toggle } = useTheme()
  const label = isDark ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <button type="button" onClick={toggle} className={`btn-ghost ${className}`} title={label} aria-label={label}>
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  )
}
