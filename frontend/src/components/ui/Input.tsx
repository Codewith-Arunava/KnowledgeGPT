/**
 * Input — Text input with icon support and error state.
 * Matches the glassmorphism design system from index.css.
 */
import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  /** Wrap the input in a labelled field group */
  wrapperClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftIcon, rightIcon, wrapperClassName, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className={clsx('flex flex-col gap-1.5', wrapperClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))] pointer-events-none">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'w-full py-2.5 rounded-xl text-sm',
              'bg-[hsl(var(--surface-elevated))] border text-[hsl(var(--text))]',
              'placeholder:text-[hsl(var(--text-muted))]',
              'focus:outline-none focus:ring-1 transition-all',
              error
                ? 'border-[hsl(var(--error)/0.6)] focus:border-[hsl(var(--error))] focus:ring-[hsl(var(--error)/0.3)]'
                : 'border-[hsl(var(--border))] focus:border-[hsl(var(--primary))] focus:ring-[hsl(var(--primary)/0.3)]',
              leftIcon ? 'pl-10' : 'pl-4',
              rightIcon ? 'pr-10' : 'pr-4',
              className,
            )}
            {...props}
          />
          {rightIcon && (
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]">
              {rightIcon}
            </span>
          )}
        </div>
        {error && (
          <p className="text-xs text-[hsl(var(--error))]">{error}</p>
        )}
        {hint && !error && (
          <p className="text-xs text-[hsl(var(--text-muted))]">{hint}</p>
        )}
      </div>
    );
  },
);

Input.displayName = 'Input';

/** Textarea variant */
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  wrapperClassName?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, wrapperClassName, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className={clsx('flex flex-col gap-1.5', wrapperClassName)}>
        {label && (
          <label htmlFor={inputId} className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={clsx(
            'w-full px-4 py-2.5 rounded-xl text-sm resize-none',
            'bg-[hsl(var(--surface-elevated))] border text-[hsl(var(--text))]',
            'placeholder:text-[hsl(var(--text-muted))]',
            'focus:outline-none focus:ring-1 transition-all',
            error
              ? 'border-[hsl(var(--error)/0.6)] focus:border-[hsl(var(--error))] focus:ring-[hsl(var(--error)/0.3)]'
              : 'border-[hsl(var(--border))] focus:border-[hsl(var(--primary))] focus:ring-[hsl(var(--primary)/0.3)]',
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-[hsl(var(--error))]">{error}</p>}
        {hint && !error && <p className="text-xs text-[hsl(var(--text-muted))]">{hint}</p>}
      </div>
    );
  },
);

Textarea.displayName = 'Textarea';
