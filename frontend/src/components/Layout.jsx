import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  BarChart3, Bell, BookOpen, ClipboardList, LayoutDashboard, LogOut, Menu, Search, Settings, X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'

export const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/study-plan', label: 'My Study Plan', icon: ClipboardList },
  { to: '/subjects', label: 'Subjects', icon: BookOpen },
  { to: '/performance', label: 'Performance', icon: BarChart3 },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join('')
}

function Sidebar({ onNavigate }) {
  const { user, logout } = useAuth()
  return (
    <div className="flex h-full flex-col bg-surface px-4 py-6">
      <div className="px-2">
        <Logo />
      </div>
      <nav className="mt-8 flex-1 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition ${
                isActive ? 'bg-primary-100 dark:bg-primary-500/15 text-primary-700 dark:text-primary-300' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-4 flex items-center gap-3 border-t border-slate-100 px-2 pt-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-500/15 text-sm font-semibold text-primary-700 dark:text-primary-300">
          {initials(user.name)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-slate-900">{user.name}</p>
          <p className="truncate text-xs text-slate-500">{user.email}</p>
        </div>
        <button onClick={logout} className="btn-ghost" title="Log out" aria-label="Log out">
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => setMobileOpen(false), [location.pathname])

  return (
    <div className="min-h-screen">
      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-slate-100 lg:block">
        <Sidebar />
      </aside>

      {/* mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-72 max-w-[85%] shadow-xl">
            <button
              onClick={() => setMobileOpen(false)}
              className="btn-ghost absolute right-3 top-3 z-10"
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-100 bg-canvas/90 px-4 py-3 backdrop-blur sm:px-6 lg:px-8">
          <button onClick={() => setMobileOpen(true)} className="btn-ghost -ml-2 lg:hidden" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
          {/* search and notifications don't do anything yet */}
          <div className="relative ml-auto w-full max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              className="input rounded-xl py-2.5 pl-9"
              placeholder="Search subjects or topics…"
              disabled
              title="Search is coming soon"
            />
          </div>
          <button className="btn-ghost relative" title="Notifications are coming soon" aria-label="Notifications">
            <Bell className="h-5 w-5" />
          </button>
          <ThemeToggle />
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
