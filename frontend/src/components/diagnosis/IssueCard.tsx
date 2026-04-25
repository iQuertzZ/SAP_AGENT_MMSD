import {
  AlertTriangle,
  AlertCircle,
  Info,
  Zap,
} from 'lucide-react'
import type { DiagnosisResult } from '../../types/sap'
import { cn } from '../../lib/utils'
import { ConfidenceBar } from '../ui/ConfidenceBar'
import { Badge } from '../ui/Badge'

interface IssueCardProps {
  diagnosis: DiagnosisResult
}

const severityIcon = {
  critical: Zap,
  high: AlertTriangle,
  medium: AlertCircle,
  low: Info,
}

const severityColors = {
  critical: { icon: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
  high: { icon: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/30' },
  medium: { icon: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/30' },
  low: { icon: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/30' },
}

const sourceLabel: Record<string, string> = {
  rule_engine: 'Moteur de règles',
  ai: 'Intelligence artificielle',
  hybrid: 'Hybride',
}

export function IssueCard({ diagnosis }: IssueCardProps) {
  const Icon = severityIcon[diagnosis.severity]
  const colors = severityColors[diagnosis.severity]

  return (
    <div className={cn('rounded-xl border p-4', colors.bg)}>
      <div className="flex items-start gap-3">
        <div className={cn('mt-0.5 shrink-0', colors.icon)}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center flex-wrap gap-2 mb-2">
            <span className="text-sm font-semibold text-text-primary">{diagnosis.issue_type.replace(/_/g, ' ')}</span>
            <Badge variant="muted">{sourceLabel[diagnosis.source] ?? diagnosis.source}</Badge>
          </div>
          <p className="text-sm text-text-secondary mb-3 leading-relaxed">{diagnosis.root_cause}</p>

          <div className="mb-3">
            <p className="text-xs text-text-muted mb-1">Niveau de confiance</p>
            <ConfidenceBar value={diagnosis.confidence} />
          </div>

          {diagnosis.supporting_evidence.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-text-muted">Éléments probants :</p>
              <ul className="space-y-0.5">
                {diagnosis.supporting_evidence.map((e, i) => (
                  <li key={i} className="text-xs text-text-secondary flex gap-1.5">
                    <span className="text-text-muted mt-0.5">·</span>
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
