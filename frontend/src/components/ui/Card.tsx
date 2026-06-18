/**
 * Card — Glassmorphism surface container.
 * Variants: glass (default), elevated, bordered, gradient
 */
import { clsx } from 'clsx';

type CardVariant = 'glass' | 'elevated' | 'bordered' | 'gradient';

interface CardProps {
  variant?: CardVariant;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const variantClasses: Record<CardVariant, string> = {
  glass: 'glass border border-[hsl(var(--border)/0.5)]',
  elevated: 'glass-elevated border border-[hsl(var(--border)/0.6)]',
  bordered: 'bg-[hsl(var(--surface))] border border-[hsl(var(--border))]',
  gradient: 'gradient-border glass',
};

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-6',
};

export function Card({
  variant = 'glass',
  children,
  className,
  onClick,
  hoverable = false,
  padding = 'md',
}: CardProps) {
  return (
    <div
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      className={clsx(
        'rounded-2xl',
        variantClasses[variant],
        paddingClasses[padding],
        hoverable && 'cursor-pointer transition-all duration-300 hover:glass-elevated',
        onClick && 'cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary)/0.5)]',
        className,
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export function CardHeader({ title, description, icon, actions, className }: CardHeaderProps) {
  return (
    <div className={clsx('flex items-start justify-between mb-4', className)}>
      <div className="flex items-center gap-2.5">
        {icon && (
          <span className="text-[hsl(var(--primary))] flex-shrink-0">{icon}</span>
        )}
        <div>
          <h2 className="text-sm font-semibold text-[hsl(var(--text))]">{title}</h2>
          {description && (
            <p className="text-xs text-[hsl(var(--text-muted))] mt-0.5">{description}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

/** Stat metric card used in Dashboard/Analytics */
interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  iconBg?: string;
  iconColor?: string;
  trend?: { value: number; direction: 'up' | 'down' };
  className?: string;
}

export function StatCard({ label, value, icon, iconBg, iconColor, trend, className }: StatCardProps) {
  return (
    <Card hoverable className={clsx('group', className)}>
      <div className="flex items-start justify-between mb-3">
        <div
          className="p-2.5 rounded-xl"
          style={{ background: iconBg || 'hsl(var(--primary)/0.1)' }}
        >
          <span style={{ color: iconColor || 'hsl(var(--primary))' }}>{icon}</span>
        </div>
      </div>
      <p className="text-2xl font-bold text-[hsl(var(--text))] mb-1">{value}</p>
      <p className="text-xs text-[hsl(var(--text-muted))]">{label}</p>
      {trend && (
        <p
          className={clsx(
            'text-xs font-medium mt-1',
            trend.direction === 'up' ? 'text-[hsl(var(--success))]' : 'text-[hsl(var(--error))]',
          )}
        >
          {trend.direction === 'up' ? '↑' : '↓'} {Math.abs(trend.value)}%
        </p>
      )}
    </Card>
  );
}
