'use client';

import { cn } from '@/lib/utils';

interface RiskBarProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

function getStyles(score: number) {
  if (score >= 70) return { color: 'bg-rose-500', text: 'text-rose-400', glow: 'shadow-glow-red' };
  if (score >= 40) return { color: 'bg-amber-500', text: 'text-amber-400', glow: 'shadow-glow-amber' };
  return { color: 'bg-emerald-500', text: 'text-emerald-400', glow: 'shadow-glow-green' };
}

export default function RiskBar({ score, size = 'sm', showLabel = true, className }: RiskBarProps) {
  const styles = getStyles(score);
  
  const heightMap = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className={cn('flex-1 rounded-full bg-slate-800/80 overflow-hidden relative', heightMap[size])}>
        {/* Track segments */}
        <div className="absolute inset-0 flex justify-between px-0.5 pointer-events-none opacity-10">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="w-[1px] h-full bg-white" />
          ))}
        </div>
        
        {/* Progress */}
        <div
          className={cn('rounded-full transition-all duration-700 ease-out relative', heightMap[size], styles.color)}
          style={{ width: `${score}%` }}
        >
          {/* Subtle shimmer */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer bg-[length:200%_100%]" />
        </div>
      </div>
      
      {showLabel && (
        <div className="min-w-[28px] text-right">
          <span className={cn('text-xs font-bold tabular-nums tracking-tighter', styles.text)}>
            {score}
          </span>
        </div>
      )}
    </div>
  );
}
