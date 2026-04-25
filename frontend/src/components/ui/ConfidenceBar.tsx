import { cn } from '../../lib/utils'

interface ConfidenceBarProps {
  value: number // 0-1
  showLabel?: boolean
  className?: string
}

export function ConfidenceBar({ value, showLabel = true, className }: ConfidenceBarProps) {
  const pct = Math.round(value * 100)

  const color =
    pct >= 80 ? 'bg-success' : pct >= 60 ? 'bg-warning' : 'bg-danger'

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-700', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className={cn('text-xs font-mono font-medium w-8 text-right', pct >= 80 ? 'text-green-400' : pct >= 60 ? 'text-orange-400' : 'text-red-400')}>
          {pct}%
        </span>
      )}
    </div>
  )
}
