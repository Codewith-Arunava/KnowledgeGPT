/**
 * Select — Native HTML select styled to match the KnowledgeGPT design system.
 * For complex dropdowns with search/multi-select, use Radix Select directly.
 */
import { forwardRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  error?: string;
  hint?: string;
  placeholder?: string;
  wrapperClassName?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, options, error, hint, placeholder, wrapperClassName, className, id, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className={clsx('flex flex-col gap-1.5', wrapperClassName)}>
        {label && (
          <label
            htmlFor={selectId}
            className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={clsx(
              'w-full pl-4 pr-10 py-2.5 rounded-xl text-sm appearance-none cursor-pointer',
              'bg-[hsl(var(--surface-elevated))] border text-[hsl(var(--text))]',
              'focus:outline-none focus:ring-1 transition-all',
              error
                ? 'border-[hsl(var(--error)/0.6)] focus:border-[hsl(var(--error))] focus:ring-[hsl(var(--error)/0.3)]'
                : 'border-[hsl(var(--border))] focus:border-[hsl(var(--primary))] focus:ring-[hsl(var(--primary)/0.3)]',
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
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown
            size={14}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))] pointer-events-none"
          />
        </div>
        {error && <p className="text-xs text-[hsl(var(--error))]">{error}</p>}
        {hint && !error && <p className="text-xs text-[hsl(var(--text-muted))]">{hint}</p>}
      </div>
    );
  },
);

Select.displayName = 'Select';
