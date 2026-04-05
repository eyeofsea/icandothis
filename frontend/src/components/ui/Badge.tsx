'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold border transition-all duration-200 uppercase tracking-tight',
  {
    variants: {
      intent: {
        default: 'border-slate-700 text-slate-400 bg-slate-800/50',
        critical: 'border-rose-500/30 text-rose-400 bg-rose-500/10',
        high: 'border-orange-500/30 text-orange-400 bg-orange-500/10',
        medium: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
        low: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
        info: 'border-sky-500/30 text-sky-400 bg-sky-500/10',
        success: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
      },
      variant: {
        solid: 'border-transparent',
        outline: 'bg-transparent',
        glass: 'backdrop-blur-md',
      },
    },
    compoundVariants: [
      { intent: 'critical', variant: 'solid', className: 'bg-rose-500 text-white' },
      { intent: 'high', variant: 'solid', className: 'bg-orange-500 text-white' },
      { intent: 'medium', variant: 'solid', className: 'bg-amber-500 text-white' },
      { intent: 'low', variant: 'solid', className: 'bg-emerald-500 text-white' },
      { intent: 'info', variant: 'solid', className: 'bg-sky-500 text-white' },
    ],
    defaultVariants: {
      intent: 'default',
      variant: 'glass',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  icon?: LucideIcon;
}

export default function Badge({ className, intent, variant, icon: Icon, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ intent, variant }), className)} {...props}>
      {Icon && <Icon className="w-2.5 h-2.5" />}
      {children}
    </span>
  );
}
