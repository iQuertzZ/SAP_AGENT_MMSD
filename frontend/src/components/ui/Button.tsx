import { type ButtonHTMLAttributes, forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, ...props }, ref) => {
    const base =
      'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue disabled:opacity-50 disabled:pointer-events-none'

    const variants = {
      primary: 'bg-accent-blue text-white hover:bg-accent-blue-hover',
      secondary:
        'bg-bg-card text-text-primary border border-border hover:border-border-strong hover:bg-white/5',
      ghost: 'text-text-secondary hover:text-text-primary hover:bg-white/5',
      danger: 'bg-danger text-white hover:bg-red-700',
      success: 'bg-success text-white hover:bg-green-700',
    }

    const sizes = {
      sm: 'px-3 py-1.5 text-xs h-7',
      md: 'px-4 py-2 text-sm h-9',
      lg: 'px-5 py-2.5 text-base h-11',
    }

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        disabled={disabled ?? loading}
        {...props}
      >
        {loading && <Loader2 className="w-4 h-4 animate-spin" />}
        {children}
      </button>
    )
  },
)
Button.displayName = 'Button'
