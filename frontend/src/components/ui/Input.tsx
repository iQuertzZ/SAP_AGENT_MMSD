import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s/g, '-')

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-text-secondary">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'h-9 px-3 rounded-lg bg-bg-secondary border text-sm text-text-primary placeholder:text-text-muted',
            'focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50',
            'transition-colors',
            error
              ? 'border-danger/60 focus:ring-danger/30'
              : 'border-border hover:border-border-strong',
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-red-400">{error}</p>}
        {hint && !error && <p className="text-xs text-text-muted">{hint}</p>}
      </div>
    )
  },
)
Input.displayName = 'Input'
