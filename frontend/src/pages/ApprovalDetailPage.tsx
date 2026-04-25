import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useApprovalDetail } from '../hooks/useApproval'
import { WorkflowTimeline } from '../components/approval/WorkflowTimeline'
import { ApprovalActions } from '../components/approval/ApprovalActions'
import { DiagnosisPanel } from '../components/diagnosis/DiagnosisPanel'
import { ActionCard } from '../components/actions/ActionCard'
import { ImpactMetrics } from '../components/simulation/ImpactMetrics'
import { Card, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { PageSpinner } from '../components/ui/Spinner'
import { formatDate } from '../lib/utils'
import { STATUS_LABEL } from '../types/approval'

const statusVariant: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'muted'> = {
  proposed: 'muted',
  awaiting_approval: 'warning',
  approved: 'success',
  rejected: 'danger',
  executed: 'info',
  rolled_back: 'muted',
  expired: 'muted',
}

export function ApprovalDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: approval, isLoading, error } = useApprovalDetail(id ?? '')

  if (isLoading) return <PageSpinner />

  if (error || !approval) {
    return (
      <div className="flex flex-col items-center justify-center min-h-64 gap-4">
        <p className="text-danger font-medium">Demande introuvable</p>
        <Link to="/approval" className="text-sm text-accent-blue hover:underline">
          ← Retour à la liste
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/approval" className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary mb-2">
            <ArrowLeft className="w-3 h-3" />
            Retour aux approbations
          </Link>
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-base font-semibold text-text-primary">
              Demande <code className="font-mono text-accent-blue">{approval.request_id.slice(0, 8)}</code>
            </h2>
            <Badge variant={statusVariant[approval.status] ?? 'muted'}>
              {STATUS_LABEL[approval.status]}
            </Badge>
          </div>
          <p className="text-xs text-text-muted mt-1">
            Soumis par {approval.requested_by ?? '—'} · {formatDate(approval.requested_at)}
          </p>
        </div>
        <ApprovalActions approval={approval} />
      </div>

      {/* Workflow Timeline */}
      <Card>
        <CardTitle className="mb-4">Progression</CardTitle>
        <WorkflowTimeline approval={approval} />
        {approval.rejection_reason && (
          <div className="mt-4 p-3 bg-danger/10 border border-danger/30 rounded-lg">
            <p className="text-xs text-red-400">
              <span className="font-semibold">Motif du rejet :</span> {approval.rejection_reason}
            </p>
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Context */}
        <Card>
          <CardTitle className="mb-3">Contexte SAP</CardTitle>
          <div className="space-y-2 text-sm">
            {[
              { label: 'TCode', value: <code className="font-mono bg-white/10 px-2 py-0.5 rounded text-accent-blue">{approval.context.tcode}</code> },
              { label: 'Module', value: approval.context.module },
              { label: 'Document', value: <code className="font-mono">{approval.context.document_id}</code> },
              { label: 'Statut', value: approval.context.status },
              approval.context.company_code && { label: 'Société', value: approval.context.company_code },
              approval.context.plant && { label: 'Usine', value: approval.context.plant },
            ].filter(Boolean).map((row) => {
              const r = row as { label: string; value: React.ReactNode }
              return (
                <div key={r.label} className="flex items-center justify-between">
                  <span className="text-text-muted">{r.label}</span>
                  <span className="text-text-primary">{r.value}</span>
                </div>
              )
            })}
          </div>
        </Card>

        {/* Diagnosis */}
        <Card>
          <CardTitle className="mb-3">Diagnostic</CardTitle>
          <DiagnosisPanel diagnosis={approval.diagnosis} />
        </Card>
      </div>

      {/* Action */}
      <Card>
        <CardTitle className="mb-3">Action recommandée</CardTitle>
        <ActionCard
          action={approval.recommended_action}
          selected
          onClick={() => undefined}
        />
      </Card>

      {/* Simulation */}
      <Card>
        <CardTitle className="mb-3">Simulation d'impact</CardTitle>
        <ImpactMetrics simulation={approval.simulation} />
      </Card>

      {/* Execution result */}
      {approval.execution_result && (
        <Card>
          <CardTitle className="mb-3">Résultat d'exécution</CardTitle>
          <div className={`p-3 rounded-lg ${approval.execution_result.success ? 'bg-success/10 border border-success/30' : 'bg-danger/10 border border-danger/30'}`}>
            <p className={`text-sm font-medium ${approval.execution_result.success ? 'text-green-400' : 'text-red-400'}`}>
              {approval.execution_result.success ? '✓ Succès' : '✕ Échec'}
            </p>
            <p className="text-xs text-text-secondary mt-1">{approval.execution_result.message}</p>
            {approval.execution_result.sap_document_number && (
              <p className="text-xs text-text-muted mt-1">
                Document SAP : <code className="font-mono">{approval.execution_result.sap_document_number}</code>
              </p>
            )}
          </div>
          {approval.execution_result.execution_log.length > 0 && (
            <div className="mt-3 space-y-1">
              {approval.execution_result.execution_log.map((entry, i) => (
                <p key={i} className="text-xs font-mono text-text-muted">{entry}</p>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
