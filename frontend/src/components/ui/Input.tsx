'use client';

import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: LucideIcon;
  error?: string;
  label?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon: Icon, error, label, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5 ml-1">
            {label}
          </label>
        )}
        <div className="relative group">
          {Icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-sky-400 transition-colors">
              <Icon className="w-4 h-4" />
            </div>
          )}
          <input
            type={type}
            className={cn(
              'flex h-10 w-full rounded-lg border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-200 ring-offset-background transition-all placeholder:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500/40 focus-visible:border-sky-500/50 disabled:cursor-not-allowed disabled:opacity-50',
              Icon && 'pl-10',
              error && 'border-rose-500/50 focus-visible:ring-rose-500/40 focus-visible:border-rose-500/50',
              className
            )}
            ref={ref}
            {...props}
          />
        </div>
        {error && <p className="mt-1 text-[10px] text-rose-400 font-medium ml-1">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
