/**
 * Spinner — Animated loading indicator.
 * Sizes: sm (12px), md (16px), lg (24px), xl (32px)
 */
import { Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

type SpinnerSize = 'sm' | 'md' | 'lg' | 'xl';

interface SpinnerProps {
  size?: SpinnerSize;
  /** Color using a Tailwind/CSS class. Defaults to primary token. */
  className?: string;
  /** Optional centered full-screen overlay */
  overlay?: boolean;
  /** Label for accessibility */
  label?: string;
}

const sizeMap: Record<SpinnerSize, number> = {
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
};

export function Spinner({ size = 'md', className, overlay = false, label = 'Loading...' }: SpinnerProps) {
  const icon = (
    <Loader2
      size={sizeMap[size]}
      className={clsx('animate-spin text-[hsl(var(--primary))]', className)}
      aria-label={label}
      role="status"
    />
  );

  if (overlay) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[hsl(var(--background)/0.8)] backdrop-blur-sm">
        {icon}
      </div>
    );
  }

  return icon;
}

/** Inline page-level skeleton placeholder */
export function SkeletonBlock({ className }: { className?: string }) {
  return <div className={clsx('skeleton rounded-xl', className)} />;
}
