import { AlertTriangle, CheckCircle, RotateCcw } from 'lucide-react'
import type { SimulationResult } from '../../types/simulation'
import { ImpactMetrics } from './ImpactMetrics'
import { Button } from '../ui/Button'

interface SimulationPanelProps {
  simulation: SimulationResult
  onSubmit: () => void
  isSubmitting?: boolean
}

export function SimulationPanel({ simulation, onSubmit, isSubmitting }: SimulationPanelProps) {
  const hasBlockers = simulation.blockers.length > 0

  return (
    <div className="space-y-4">
      <ImpactMetrics simulation={simulation} />

      {simulation.warnings.length > 0 && (
        <div className="bg-warning/10 border border-warning/30 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-orange-400 text-sm font-medium">
            <AlertTriangle className="w-4 h-4" />
            Avertissements ({simulation.warnings.length})
          </div>
          <ul className="space-y-1">
            {simulation.warnings.map((w, i) => (
              <li key={i} className="text-xs text-orange-300 flex gap-1.5">
                <span className="mt-0.5 text-orange-500">·</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasBlockers && (
        <div className="bg-danger/10 border border-danger/30 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-red-400 text-sm font-medium">
            <AlertTriangle className="w-4 h-4" />
            Blocages — exécution impossible
          </div>
          <ul className="space-y-1">
            {simulation.blockers.map((b, i) => (
              <li key={i} className="text-xs text-red-300 flex gap-1.5">
                <span className="mt-0.5 text-red-500">·</span>
                {b}
              </li>
            ))}
          </ul>
        </div>
      )}

      {simulation.reversible && (
        <div className="flex items-center gap-2 text-xs text-green-400">
          <RotateCcw className="w-3.5 h-3.5" />
          Action réversible — rollback disponible
        </div>
      )}

      {simulation.simulation_notes && (
        <p className="text-xs text-text-muted border-l-2 border-border pl-3">
          {simulation.simulation_notes}
        </p>
      )}

      <Button
        variant="primary"
        size="lg"
        className="w-full"
        onClick={onSubmit}
        loading={isSubmitting}
        disabled={hasBlockers}
      >
        <CheckCircle className="w-4 h-4" />
        Soumettre pour approbation
      </Button>
    </div>
  )
}
