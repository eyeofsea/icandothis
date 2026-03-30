'use client';

import { Shield, Route, DollarSign, Navigation, BarChart3 } from 'lucide-react';

interface QuickActionsProps {
  onAction: (text: string) => void;
}

const ACTIONS = [
  { label: "What's at risk?", icon: Shield, text: "What equipment and projects are currently at risk?" },
  { label: 'Alternatives', icon: Route, text: "Show me alternative suppliers for critical equipment" },
  { label: 'Cost impact?', icon: DollarSign, text: "What is the cost impact of current risk factors?" },
  { label: 'Reroute', icon: Navigation, text: "What are the reroute options for high-risk shipping lanes?" },
  { label: 'Full analysis', icon: BarChart3, text: "Run a full risk analysis on the current portfolio" },
];

export default function QuickActions({ onAction }: QuickActionsProps) {
  return (
    <div className="px-4 py-2 flex gap-1.5 overflow-x-auto">
      {ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => onAction(action.text)}
          className="flex items-center gap-1 px-2 py-1 rounded-full bg-[#1a2236] border border-[#1e3a5f]/50 hover:border-blue-500/30 hover:bg-blue-500/5 text-[9px] text-slate-400 hover:text-slate-200 whitespace-nowrap transition-colors"
        >
          <action.icon className="w-2.5 h-2.5" />
          {action.label}
        </button>
      ))}
    </div>
  );
}
