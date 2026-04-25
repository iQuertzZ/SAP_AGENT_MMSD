import { useLocation, Link } from 'react-router-dom'
import { Plus } from 'lucide-react'

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/analyze': 'Analyse SAP',
  '/approval': 'Approbations',
  '/admin': 'Administration',
}

export function TopBar() {
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] ?? (pathname.startsWith('/approval/') ? 'Détail approbation' : 'SAP Copilot')

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-border bg-bg-secondary shrink-0">
      <h1 className="text-sm font-semibold text-text-primary">{title}</h1>
      {pathname !== '/analyze' && (
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-3 py-1.5 bg-accent-blue text-white text-xs font-medium rounded-lg hover:bg-accent-blue-hover transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Nouvelle analyse
        </Link>
      )}
    </header>
  )
}
