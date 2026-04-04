'use client';

import { cn } from '@/lib/utils';

interface RiskBarProps {
  score: number;
  size?: 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
}

function barColor(score: number): string {
  if (score >= 70) return '#ef4444';
  if (score >= 50) return '#f97316';
  if (score >= 30) return '#eab308';
  return '#22c55e';
}

function textColor(score: number): string {
  if (score >= 70) return 'text-red-400';
  if (score >= 50) return 'text-orange-400';
  if (score >= 30) return 'text-yellow-400';
  return 'text-green-400';
}

export default function RiskBar({ score, size = 'sm', showLabel = true, className }: RiskBarProps) {
  const h = size === 'sm' ? 'h-1.5' : 'h-2.5';

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={`flex-1 ${h} rounded-full bg-slate-700 overflow-hidden`}>
        <div
          className={`${h} rounded-full transition-all duration-500`}
          style={{ width: `${score}%`, background: barColor(score) }}
        />
      </div>
      {showLabel && <span className={`text-xs font-semibold tabular-nums ${textColor(score)}`}>{score}</span>}
    </div>
  );
}
