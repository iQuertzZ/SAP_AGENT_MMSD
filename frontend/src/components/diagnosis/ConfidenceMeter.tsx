import { cn } from '../../lib/utils'

interface ConfidenceMeterProps {
  value: number // 0-1
  size?: number
  className?: string
}

export function ConfidenceMeter({ value, size = 80, className }: ConfidenceMeterProps) {
  const pct = Math.round(value * 100)
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  const color = pct >= 80 ? '#1E8C4E' : pct >= 60 ? '#E76500' : '#BB0000'

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={6}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      <span className="absolute text-sm font-mono font-semibold" style={{ color }}>
        {pct}%
      </span>
    </div>
  )
}
