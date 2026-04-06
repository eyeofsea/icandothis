'use client';

import { Bot } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useFeedStore } from '@/stores/feedStore';
import { cn } from '@/lib/utils';

const STATUS_CONFIG = {
  idle: {
    dot: 'bg-emerald-400',
    label: 'Idle',
    labelColor: 'text-emerald-400',
  },
  analyzing: {
    dot: 'bg-amber-400 animate-pulse',
    label: 'Analyzing',
    labelColor: 'text-amber-400',
  },
  completed: {
    dot: 'bg-sky-400',
    label: 'Completed',
    labelColor: 'text-sky-400',
  },
  error: {
    dot: 'bg-red-400',
    label: 'Error',
    labelColor: 'text-red-400',
  },
} as const;

export default function AgentActivityPanel() {
  const agentStatuses = useFeedStore((s) => s.agentStatuses);

  const activeCount = agentStatuses.filter(
    (a) => a.status === 'analyzing'
  ).length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-2">
        <Bot className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Agent Activity
        </span>
        <span className="ml-auto text-[9px] text-slate-500">
          {activeCount}/{agentStatuses.length} active
        </span>
      </div>
      <div className="flex-1 overflow-y-auto space-y-1.5">
        {agentStatuses.map((agent) => {
          const config = STATUS_CONFIG[agent.status];
          return (
            <div
              key={agent.name}
              className="flex items-start gap-2 p-2 rounded-md border bg-slate-800/40 border-slate-700/50"
            >
              <span
                className={cn(
                  'w-2 h-2 rounded-full flex-shrink-0 mt-1',
                  config.dot
                )}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-medium text-slate-300">
                    {agent.name}
                  </span>
                  <span
                    className={cn(
                      'text-[9px] font-medium',
                      config.labelColor
                    )}
                  >
                    {config.label}
                  </span>
                </div>
                {agent.lastTask && (
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5 truncate">
                    {agent.lastTask}
                  </p>
                )}
                {agent.resultSummary && (
                  <p className="text-[10px] text-slate-400 leading-tight mt-0.5 truncate">
                    {agent.resultSummary}
                  </p>
                )}
                {agent.lastRun && (
                  <span className="text-[9px] text-slate-600 mt-0.5 block">
                    {formatDistanceToNow(new Date(agent.lastRun), {
                      addSuffix: true,
                    })}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
