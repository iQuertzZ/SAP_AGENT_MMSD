import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Clock, CheckCircle, PlayCircle, TrendingUp } from 'lucide-react'
import { useApprovalList } from '../hooks/useApproval'
import { useAuthStore } from '../store/auth.store'
import { Card, CardHeader, CardTitle } from '../components/ui/Card'
import { ApprovalCard } from '../components/approval/ApprovalCard'
import { PageSpinner } from '../components/ui/Spinner'

export function DashboardPage() {
  const { user } = useAuthStore()
  const { data, isLoading } = useApprovalList()

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return
      if (e.key === 'n' || e.key === 'N') {
        window.location.href = '/analyze'
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  if (isLoading) return <PageSpinner />

  const items = data?.items ?? []
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)

  const pending = items.filter((r) => r.status === 'awaiting_approval').length
  const approvedToday = items.filter(
    (r) => r.status === 'approved' && r.approval_timestamp && new Date(r.approval_timestamp) >= todayStart,
  ).length
  const executedMonth = items.filter(
    (r) => r.status === 'executed' && r.execution_result && new Date(r.execution_result.executed_at) >= monthStart,
  ).length
  const avgRisk =
    items.length > 0
      ? (items.reduce((acc, r) => acc + r.simulation.risk_score, 0) / items.length) * 100
      : 0

  const stats = [
    { label: 'En attente', value: pending, icon: Clock, color: 'text-orange-400' },
    { label: "Approuvées aujourd'hui", value: approvedToday, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Exécutées ce mois', value: executedMonth, icon: PlayCircle, color: 'text-blue-400' },
    { label: 'Risque moyen', value: `${avgRisk.toFixed(0)}%`, icon: TrendingUp, color: 'text-text-secondary' },
  ]

  const recent = [...items].sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime()).slice(0, 5)

  return (
    <div className="max-w-5xl space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">
            Bonjour, <span className="text-accent-blue">{user?.email.split('@')[0]}</span>
          </h2>
          <p className="text-sm text-text-secondary mt-0.5">Rôle : {user?.role}</p>
        </div>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-4 py-2 bg-accent-blue text-white text-sm font-medium rounded-lg hover:bg-accent-blue-hover transition-colors"
        >
          <Plus className="w-4 h-4" />
          Nouvelle analyse <span className="text-white/50 text-xs">N</span>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-white/5 ${color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-2xl font-bold text-text-primary">{value}</p>
                <p className="text-xs text-text-secondary">{label}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Recent */}
      <Card>
        <CardHeader>
          <CardTitle>Demandes récentes</CardTitle>
          <Link to="/approval" className="text-xs text-text-secondary hover:text-text-primary transition-colors">
            Voir tout →
          </Link>
        </CardHeader>
        {recent.length === 0 ? (
          <div className="py-8 text-center text-sm text-text-muted">
            Aucune demande. <Link to="/analyze" className="text-accent-blue hover:underline">Lancer une analyse</Link>
          </div>
        ) : (
          <div className="space-y-2">
            {recent.map((a) => (
              <ApprovalCard key={a.request_id} approval={a} />
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
