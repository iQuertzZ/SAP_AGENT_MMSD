import { Clock, Shield, ChevronRight } from 'lucide-react'
import type { RecommendedAction } from '../../types/sap'
import { cn } from '../../lib/utils'
import { ConfidenceBar } from '../ui/ConfidenceBar'
import { RiskBadge } from './RiskBadge'

interface ActionCardProps {
  action: RecommendedAction
  selected?: boolean
  onClick: () => void
}

export function ActionCard({ action, selected, onClick }: ActionCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'group relative p-4 rounded-xl border cursor-pointer transition-all',
        selected
          ? 'border-accent-blue bg-accent-blue/10'
          : 'border-border bg-bg-card hover:border-border-strong hover:bg-white/[0.02]',
      )}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <code className="text-xs font-mono bg-white/10 px-2 py-0.5 rounded text-accent-blue">
              {action.tcode}
            </code>
            <RiskBadge level={action.risk} />
          </div>
          <p className="text-sm text-text-primary font-medium leading-snug">{action.description}</p>
        </div>
        <ChevronRight
          className={cn(
            'w-4 h-4 shrink-0 mt-0.5 transition-colors',
            selected ? 'text-accent-blue' : 'text-text-muted group-hover:text-text-secondary',
          )}
        />
      </div>

      <ConfidenceBar value={action.confidence} className="mb-3" />

      <div className="flex items-center justify-between text-xs text-text-muted">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          ~{action.estimated_duration_minutes} min
        </div>
        {action.requires_authorization.length > 0 && (
          <div className="flex items-center gap-1">
            <Shield className="w-3 h-3" />
            {action.requires_authorization.length} auth requise(s)
          </div>
        )}
      </div>

      {/* Rollback plan tooltip */}
      <div className="mt-3 pt-3 border-t border-border">
        <p className="text-xs text-text-muted">
          <span className="text-green-400 font-medium">Rollback : </span>
          {action.rollback_plan}
        </p>
      </div>
    </div>
  )
}
