/**
 * Modal — Glassmorphism dialog built on Radix UI Dialog primitive.
 * Handles focus trap, keyboard escape, and backdrop blur automatically.
 */
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  /** Max-width class — defaults to max-w-md */
  maxWidth?: string;
  className?: string;
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  maxWidth = 'max-w-md',
  className,
}: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        {/* Backdrop */}
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-fade-in" />

        {/* Content */}
        <Dialog.Content
          className={clsx(
            'fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-full p-6',
            'glass-elevated rounded-2xl shadow-2xl border border-[hsl(var(--border)/0.6)]',
            'animate-fade-in focus:outline-none',
            maxWidth,
            className,
          )}
        >
          {/* Header */}
          {(title || description) && (
            <div className="mb-5">
              <div className="flex items-center justify-between">
                {title && (
                  <Dialog.Title className="text-lg font-semibold text-[hsl(var(--text))]">
                    {title}
                  </Dialog.Title>
                )}
                <Dialog.Close asChild>
                  <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--border)/0.5)] transition-all"
                    aria-label="Close modal"
                  >
                    <X size={16} />
                  </button>
                </Dialog.Close>
              </div>
              {description && (
                <Dialog.Description className="text-sm text-[hsl(var(--text-muted))] mt-1">
                  {description}
                </Dialog.Description>
              )}
            </div>
          )}

          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

/** Convenience footer for modal action buttons */
export function ModalFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx('flex gap-3 mt-6', className)}>
      {children}
    </div>
  );
}
