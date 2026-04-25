import { FileText, BookOpen } from 'lucide-react'
import type { SimulationResult } from '../../types/simulation'
import { formatCurrency } from '../../lib/utils'
import { ConfidenceMeter } from '../diagnosis/ConfidenceMeter'
import { Badge } from '../ui/Badge'

interface ImpactMetricsProps {
  simulation: SimulationResult
}

export function ImpactMetrics({ simulation }: ImpactMetricsProps) {
  const { financial } = simulation

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Documents affected */}
      <div className="bg-bg-secondary rounded-xl p-4 flex flex-col items-center gap-2">
        <FileText className="w-5 h-5 text-text-muted" />
        <span className="text-2xl font-bold text-text-primary">{simulation.documents_affected}</span>
        <span className="text-xs text-text-muted text-center">Documents affectés</span>
      </div>

      {/* Financial impact */}
      <div className="bg-bg-secondary rounded-xl p-4 flex flex-col items-center gap-2">
        <div className="flex items-center gap-1">
          <BookOpen className="w-5 h-5 text-text-muted" />
          {financial.posting_required && (
            <Badge variant="warning" className="text-[10px]">Écriture</Badge>
          )}
        </div>
        <span className="text-xl font-bold text-text-primary font-mono">
          {formatCurrency(financial.amount, financial.currency ?? 'EUR')}
        </span>
        <span className="text-xs text-text-muted">Impact financier</span>
      </div>

      {/* Risk score gauge */}
      <div className="bg-bg-secondary rounded-xl p-4 flex flex-col items-center gap-2">
        <ConfidenceMeter value={simulation.risk_score} size={64} />
        <span className="text-xs text-text-muted">Score de risque</span>
      </div>
    </div>
  )
}
