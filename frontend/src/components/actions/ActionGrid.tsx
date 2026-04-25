import type { RecommendedAction } from '../../types/sap'
import { ActionCard } from './ActionCard'

interface ActionGridProps {
  actions: RecommendedAction[]
  selectedId: string | null
  onSelect: (action: RecommendedAction) => void
}

export function ActionGrid({ actions, selectedId, onSelect }: ActionGridProps) {
  if (actions.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-text-muted text-sm">
        Aucune action recommandée pour ce document.
      </div>
    )
  }

  const sorted = [...actions].sort((a, b) => b.confidence - a.confidence)

  return (
    <div className="space-y-3">
      {sorted.map((action) => (
        <ActionCard
          key={action.action_id}
          action={action}
          selected={selectedId === action.action_id}
          onClick={() => onSelect(action)}
        />
      ))}
    </div>
  )
}
