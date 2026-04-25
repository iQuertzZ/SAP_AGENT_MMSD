import { useNavigate } from 'react-router-dom'
import type { ApprovalRequest } from '../../types/approval'
import { STATUS_LABEL } from '../../types/approval'
import { formatRelativeTime } from '../../lib/utils'
import { RiskBadge } from '../actions/RiskBadge'
import { Badge } from '../ui/Badge'

interface ApprovalCardProps {
  approval: ApprovalRequest
}

const statusVariant: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'muted'> = {
  proposed: 'muted',
  awaiting_approval: 'warning',
  approved: 'success',
  rejected: 'danger',
  executed: 'info',
  rolled_back: 'muted',
  expired: 'muted',
}

export function ApprovalCard({ approval }: ApprovalCardProps) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/approval/${approval.request_id}`)}
      className="flex items-center gap-4 p-4 bg-bg-card border border-border rounded-xl cursor-pointer hover:border-border-strong hover:bg-white/[0.02] transition-colors"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <code className="text-xs font-mono bg-white/10 px-2 py-0.5 rounded text-accent-blue">
            {approval.context.tcode}
          </code>
          <span className="text-xs text-text-muted font-mono">{approval.context.document_id}</span>
          <Badge variant={statusVariant[approval.status] ?? 'muted'}>
            {STATUS_LABEL[approval.status]}
          </Badge>
        </div>
        <p className="text-sm text-text-primary truncate">{approval.diagnosis.root_cause}</p>
        <p className="text-xs text-text-muted mt-0.5">
          {approval.requested_by} · {formatRelativeTime(approval.requested_at)}
        </p>
      </div>
      <RiskBadge level={approval.recommended_action.risk} />
    </div>
  )
}
