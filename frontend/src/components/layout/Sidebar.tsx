import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  CheckSquare,
  Settings,
  LogOut,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../hooks/useAuth'
import { useApprovalList } from '../../hooks/useApproval'
import { Badge } from '../ui/Badge'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
  { to: '/analyze', icon: Search, label: 'Analyser' },
  { to: '/approval', icon: CheckSquare, label: 'Approbations' },
]

export function Sidebar() {
  const { user, logout } = useAuth()
  const { data: approvals } = useApprovalList(true)
  const pendingCount = approvals?.total ?? 0

  return (
    <aside className="flex flex-col w-56 min-h-screen bg-bg-secondary border-r border-border shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 h-14 border-b border-border">
        <span className="text-accent-blue text-lg">◈</span>
        <span className="text-sm font-semibold text-text-primary">
          SAP <span className="text-accent-blue">MM/SD</span> Copilot
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              cn(
                'flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-accent-blue/15 text-accent-blue font-medium'
                  : 'text-text-secondary hover:text-text-primary hover:bg-white/5',
              )
            }
          >
            <span className="flex items-center gap-2">
              <Icon className="w-4 h-4" />
              {label}
            </span>
            {label === 'Approbations' && pendingCount > 0 && (
              <Badge variant="warning">{pendingCount}</Badge>
            )}
          </NavLink>
        ))}

        {user?.role === 'admin' && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-accent-blue/15 text-accent-blue font-medium'
                  : 'text-text-secondary hover:text-text-primary hover:bg-white/5',
              )
            }
          >
            <Settings className="w-4 h-4" />
            Administration
          </NavLink>
        )}
      </nav>

      {/* User footer */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-2 px-2 py-1.5 mb-1">
          <div className="w-7 h-7 rounded-full bg-accent-blue/20 flex items-center justify-center text-xs font-semibold text-accent-blue">
            {user?.email.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-text-primary truncate">{user?.email}</p>
            <p className="text-xs text-text-muted capitalize">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={() => void logout()}
          className="flex items-center gap-2 w-full px-3 py-1.5 rounded-lg text-xs text-text-secondary hover:text-text-primary hover:bg-white/5 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Déconnexion
        </button>
      </div>
    </aside>
  )
}
