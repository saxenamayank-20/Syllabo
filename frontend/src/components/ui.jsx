import { useEffect } from 'react'
import { Loader2, X } from 'lucide-react'

export function Spinner({ className = 'h-5 w-5' }) {
  return <Loader2 className={`animate-spin text-primary-600 ${className}`} aria-label="Loading" />
}

export function LoadingBlock({ label = 'Loading…', className = 'py-10' }) {
  return (
    <div className={`flex items-center justify-center gap-2 text-sm text-slate-500 ${className}`}>
      <Spinner className="h-4 w-4" /> {label}
    </div>
  )
}

export function EmptyState({ icon: Icon, title, hint, action, className = 'py-10' }) {
  return (
    <div className={`flex flex-col items-center justify-center text-center ${className}`}>
      {Icon && (
        <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-400">
          <Icon className="h-5 w-5" />
        </div>
      )}
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {hint && <p className="mt-1 max-w-xs text-xs text-slate-500">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function CardHeader({ title, icon: Icon, action }) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900 sm:text-lg">
        {Icon && <Icon className="h-5 w-5 text-slate-500" />}
        {title}
      </h2>
      {action}
    </div>
  )
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Modal({ open, title, onClose, children, footer, wide = false }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-surface shadow-xl dark:ring-1 dark:ring-white/10 sm:rounded-2xl ${wide ? 'sm:max-w-2xl' : 'sm:max-w-md'}`}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h3 className="text-base font-semibold text-slate-900">{title}</h3>
          <button onClick={onClose} className="btn-ghost -mr-2" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Delete', busy, onConfirm, onClose }) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" onClick={onClose} disabled={busy}>Cancel</button>
          <button className="btn-danger" onClick={onConfirm} disabled={busy}>
            {busy && <Spinner className="h-4 w-4 text-white" />} {confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-sm text-slate-600">{message}</p>
    </Modal>
  )
}

export function Checkbox({ checked, onChange, disabled, label }) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={onChange}
      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md border-2 transition disabled:opacity-50 ${
        checked ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300 bg-surface hover:border-emerald-400'
      }`}
    >
      {checked && (
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M3.5 8.5l3 3 6-7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  )
}

export function SubjectDot({ color }) {
  return <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />
}
