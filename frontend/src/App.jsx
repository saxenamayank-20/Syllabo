import { Navigate, Route, Routes } from 'react-router-dom'
import { Bot, CalendarDays, NotebookPen, Settings } from 'lucide-react'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import ComingSoon from './pages/ComingSoon'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Performance from './pages/Performance'
import Register from './pages/Register'
import StudyPlan from './pages/StudyPlan'
import Subjects from './pages/Subjects'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="study-plan" element={<StudyPlan />} />
          <Route path="subjects" element={<Subjects />} />
          <Route path="performance" element={<Performance />} />
          <Route path="assistant" element={<ComingSoon title="AI Assistant" icon={Bot} />} />
          <Route path="calendar" element={<ComingSoon title="Calendar" icon={CalendarDays} />} />
          <Route path="notes" element={<ComingSoon title="Notes" icon={NotebookPen} />} />
          <Route path="settings" element={<ComingSoon title="Settings" icon={Settings} />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
