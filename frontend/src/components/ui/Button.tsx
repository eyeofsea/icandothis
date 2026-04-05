'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { LucideIcon, Loader2 } from 'lucide-react';
import { ButtonHTMLAttributes, forwardRef } from 'react';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-sky-500/40 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary: 'bg-sky-500 text-white hover:bg-sky-400 shadow-glow-blue border border-sky-400/20',
        secondary: 'bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-700',
        outline: 'bg-transparent border border-slate-700 text-slate-300 hover:border-slate-500 hover:text-slate-100',
        ghost: 'bg-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/50',
        danger: 'bg-rose-500 text-white hover:bg-rose-400 shadow-glow-red border border-rose-400/20',
        glass: 'glass-card-pro hover:bg-white/5 text-slate-200 border-white/10',
      },
      size: {
        xs: 'px-2 py-1 text-[10px]',
        sm: 'px-3 py-1.5 text-xs',
        md: 'px-4 py-2 text-sm',
        lg: 'px-6 py-3 text-base',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  icon?: LucideIcon;
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, icon: Icon, loading, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={loading || props.disabled}
        {...props}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : Icon ? (
          <Icon className={cn('w-4 h-4', size === 'xs' && 'w-3 h-3')} />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
