'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'outline';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export default function Card({
  title,
  subtitle,
  description,
  children,
  footer,
  className,
  variant = 'glass',
  padding = 'md',
}: CardProps) {
  const paddingMap = {
    none: 'p-0',
    sm: 'p-3',
    md: 'p-5',
    lg: 'p-8',
  };

  return (
    <div
      className={cn(
        'relative rounded-xl overflow-hidden transition-all duration-300',
        variant === 'glass' && 'glass-card-pro shadow-glass hover:shadow-glow-blue/10',
        variant === 'outline' && 'border border-slate-700 bg-slate-900/40',
        variant === 'default' && 'bg-slate-900 border border-slate-800',
        className
      )}
    >
      {(title || subtitle || description) && (
        <div className="px-5 py-4 border-b border-white/5 bg-white/2">
          {title && (
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">{title}</h3>
              {subtitle && <div className="text-xs text-slate-500">{subtitle}</div>}
            </div>
          )}
          {description && <p className="mt-1 text-xs text-slate-500">{description}</p>}
        </div>
      )}

      <div className={paddingMap[padding]}>{children}</div>

      {footer && (
        <div className="px-5 py-3 border-t border-white/5 bg-slate-950/20">
          {footer}
        </div>
      )}
    </div>
  );
}
