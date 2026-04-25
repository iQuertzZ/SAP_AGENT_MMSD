import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  label?: string
}

export function Spinner({ size = 'md', className, label }: SpinnerProps) {
  const sizes = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }

  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <Loader2 className={cn('animate-spin text-accent-blue', sizes[size])} />
      {label && <p className="text-sm text-text-secondary">{label}</p>}
    </div>
  )
}

export function PageSpinner({ label = 'Chargement…' }: { label?: string }) {
  return (
    <div className="flex-1 flex items-center justify-center min-h-64">
      <Spinner size="lg" label={label} />
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-4 animate-pulse">
      <div className="h-4 bg-white/10 rounded w-3/4 mb-3" />
      <div className="h-3 bg-white/5 rounded w-full mb-2" />
      <div className="h-3 bg-white/5 rounded w-5/6" />
    </div>
  )
}
