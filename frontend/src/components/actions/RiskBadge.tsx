import type { RiskLevel } from '../../types/sap'
import { cn } from '../../lib/utils'

interface RiskBadgeProps {
  level: RiskLevel
  className?: string
}

const config: Record<RiskLevel, { dot: string; text: string; bg: string }> = {
  low: { dot: 'bg-green-400', text: 'text-green-400', bg: 'bg-green-400/10 border-green-400/20' },
  medium: { dot: 'bg-orange-400', text: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/20' },
  high: { dot: 'bg-red-400', text: 'text-red-400', bg: 'bg-red-400/10 border-red-400/20' },
}

const labels: Record<RiskLevel, string> = {
  low: 'Faible',
  medium: 'Moyen',
  high: 'Élevé',
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  const c = config[level]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border',
        c.bg,
        c.text,
        className,
      )}
    >
      <span className={cn('w-1.5 h-1.5 rounded-full', c.dot)} />
      {labels[level]}
    </span>
  )
}
