import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/auth.store'
import type { SAPRole } from '../../types/auth'
import { hasMinRole } from '../../types/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
  minRole?: SAPRole
}

export function ProtectedRoute({ children, minRole }: ProtectedRouteProps) {
  const { user, accessToken } = useAuthStore()
  const location = useLocation()

  if (!accessToken || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (minRole && !hasMinRole(user.role, minRole)) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-64">
        <div className="text-center space-y-2">
          <p className="text-lg font-semibold text-danger">Accès refusé</p>
          <p className="text-sm text-text-secondary">
            Votre rôle <span className="font-mono text-text-primary">{user.role}</span> ne permet pas
            d'accéder à cette page.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
