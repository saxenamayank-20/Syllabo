import { render } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import { ToastProvider } from '../context/ToastContext'

function LocationProbe() {
  const location = useLocation()
  return <div data-testid="location">{location.pathname + location.search}</div>
}

/** Render `element` at `path` inside the app providers; a probe shows the current URL. */
export function renderAt(path, element, { route = path.split('?')[0] } = {}) {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <ToastProvider>
          <AuthProvider>
            <Routes>
              <Route path={route} element={element} />
              <Route path="*" element={<p>other page</p>} />
            </Routes>
            <LocationProbe />
          </AuthProvider>
        </ToastProvider>
      </MemoryRouter>
    </ThemeProvider>,
  )
}

export function axiosError(status, detail) {
  return Object.assign(new Error('Request failed'), { response: { status, data: { detail } } })
}
