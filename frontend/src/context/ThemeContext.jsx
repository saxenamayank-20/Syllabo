import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

export const THEME_KEY = 'syllabo_theme'

const ThemeContext = createContext(null)

function systemPrefersDark() {
  return Boolean(window.matchMedia?.('(prefers-color-scheme: dark)').matches)
}

function savedTheme() {
  try {
    const value = localStorage.getItem(THEME_KEY)
    return value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

// follows the device until the user picks a theme, then remembers it
export function ThemeProvider({ children }) {
  const [choice, setChoice] = useState(savedTheme)
  const [systemDark, setSystemDark] = useState(systemPrefersDark)
  const theme = choice ?? (systemDark ? 'dark' : 'light')

  useEffect(() => {
    const mq = window.matchMedia?.('(prefers-color-scheme: dark)')
    if (!mq) return
    const onChange = (e) => setSystemDark(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  const toggle = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setChoice(next)
    try {
      localStorage.setItem(THEME_KEY, next)
    } catch {
      // storage blocked (private mode), still works for this visit
    }
  }, [theme])

  const value = useMemo(() => ({ theme, isDark: theme === 'dark', toggle }), [theme, toggle])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
