import { cn } from '../../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'muted'
  className?: string
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  const variants = {
    default: 'bg-white/10 text-text-primary',
    success: 'bg-success/15 text-green-400 border border-success/30',
    warning: 'bg-warning/15 text-orange-400 border border-warning/30',
    danger: 'bg-danger/15 text-red-400 border border-danger/30',
    info: 'bg-accent-blue/15 text-blue-400 border border-accent-blue/30',
    muted: 'bg-white/5 text-text-secondary',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}
