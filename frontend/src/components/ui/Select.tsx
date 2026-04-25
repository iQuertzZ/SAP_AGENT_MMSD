import { forwardRef, type SelectHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface SelectOption {
  value: string
  label: string
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: SelectOption[]
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, id, ...props }, ref) => {
    const selectId = id ?? label?.toLowerCase().replace(/\s/g, '-')

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={selectId} className="text-xs font-medium text-text-secondary">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'h-9 px-3 rounded-lg bg-bg-secondary border text-sm text-text-primary',
            'focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50',
            'transition-colors appearance-none cursor-pointer',
            error
              ? 'border-danger/60 focus:ring-danger/30'
              : 'border-border hover:border-border-strong',
            className,
          )}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>
    )
  },
)
Select.displayName = 'Select'
