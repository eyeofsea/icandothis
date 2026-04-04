'use client';

import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface StatRowProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color?: string;
  className?: string;
}

export default function StatRow({ icon: Icon, label, value, color = 'text-cyan-400', className }: StatRowProps) {
  return (
    <div className={cn('flex items-center justify-between py-2 border-b border-[#1e3a5f]/40 last:border-0', className)}>
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Icon className={`w-3.5 h-3.5 ${color}`} />
        <span>{label}</span>
      </div>
      <span className="text-xs font-semibold text-slate-200">{value}</span>
    </div>
  );
}
