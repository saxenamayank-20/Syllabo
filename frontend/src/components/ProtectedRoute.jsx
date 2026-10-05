import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LoadingBlock } from './ui'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <LoadingBlock className="h-screen" />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}
