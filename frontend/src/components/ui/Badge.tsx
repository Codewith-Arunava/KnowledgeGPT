/**
 * Badge — Pill label for statuses, tags, and counts.
 * Variants map to the KnowledgeGPT CSS HSL color tokens.
 */
import { clsx } from 'clsx';

type BadgeVariant =
  | 'default'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'error'
  | 'muted';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-[hsl(var(--surface-elevated))] text-[hsl(var(--text-muted))] border border-[hsl(var(--border))]',
  primary: 'bg-[hsl(var(--primary)/0.1)] text-[hsl(var(--primary))] border border-[hsl(var(--primary)/0.3)]',
  secondary: 'bg-[hsl(var(--secondary)/0.1)] text-[hsl(var(--secondary))] border border-[hsl(var(--secondary)/0.3)]',
  success: 'bg-[hsl(var(--success)/0.1)] text-[hsl(var(--success))] border border-[hsl(var(--success)/0.3)]',
  warning: 'bg-[hsl(var(--warning)/0.1)] text-[hsl(var(--warning))] border border-[hsl(var(--warning)/0.3)]',
  error: 'bg-[hsl(var(--error)/0.1)] text-[hsl(var(--error))] border border-[hsl(var(--error)/0.3)]',
  muted: 'bg-[hsl(var(--surface-elevated))] text-[hsl(var(--text-muted))]',
};

export function Badge({ variant = 'default', children, icon, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        variantClasses[variant],
        className,
      )}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
}
