'use client';

import { useState } from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  FolderKanban,
  Bell,
  Newspaper,
  Globe,
  GitFork,
  Zap,
  FlaskConical,
  Scale,
  Radar,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import Tooltip from '@/components/ui/Tooltip';
import { cn } from '@/lib/utils';

export type ViewId = 'dashboard' | 'riskmatrix' | 'projects' | 'alerts' | 'news' | 'map' | 'ontology' | 'impact' | 'scenario' | 'hedging';

interface NavItem {
  id: ViewId;
  label: string;
  icon: typeof LayoutDashboard;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'riskmatrix', label: 'Risk Matrix', icon: ShieldAlert },
  { id: 'projects', label: 'Projects', icon: FolderKanban },
  { id: 'alerts', label: 'Alerts', icon: Bell },
  { id: 'news', label: 'News', icon: Newspaper },
  { id: 'map', label: 'Map', icon: Globe },
  { id: 'ontology', label: 'Ontology', icon: GitFork },
  { id: 'impact', label: 'Impact', icon: Zap },
  { id: 'scenario', label: 'Scenario', icon: FlaskConical },
  { id: 'hedging', label: 'Hedging Report', icon: Scale },
];

interface SidebarProps {
  activeView: ViewId;
  onViewChange: (view: ViewId) => void;
  alertCount?: number;
}

export default function Sidebar({ activeView, onViewChange, alertCount = 0 }: SidebarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <aside 
      className={cn(
        "h-screen flex-shrink-0 bg-slate-950 border-r border-slate-800/60 flex flex-col transition-all duration-300 ease-in-out z-[100]",
        isExpanded ? "w-64" : "w-16"
      )}
    >
      {/* Header / Logo */}
      <div className="h-14 flex items-center px-4 mb-4">
        <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center border border-sky-400/20 shadow-glow-blue/10">
          <Radar className="w-5 h-5 text-sky-400" strokeWidth={2.5} />
        </div>
        {isExpanded && (
          <span className="ml-3 font-bold text-white tracking-tight text-sm uppercase">Risk Intel</span>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex flex-col gap-1.5 px-3 flex-1 overflow-y-auto scrollbar-hide">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          const Icon = item.icon;

          const content = (
            <button
              onClick={() => onViewChange(item.id)}
              className={cn(
                'group relative w-full h-10 flex items-center rounded-lg transition-all duration-200 outline-none',
                isActive
                  ? 'bg-sky-500/10 text-sky-400 border border-sky-400/20'
                  : 'text-slate-500 hover:text-slate-200 hover:bg-white/5 border border-transparent'
              )}
            >
              <div className="min-w-[40px] flex items-center justify-center">
                <Icon className={cn('w-4 h-4 transition-transform duration-200 group-hover:scale-110', isActive && 'text-sky-400')} strokeWidth={isActive ? 2.5 : 2} />
              </div>
              
              {isExpanded && (
                <span className={cn('ml-1 text-xs font-semibold tracking-wide truncate', isActive && 'text-slate-100')}>
                  {item.label}
                </span>
              )}

              {/* Alert Badge */}
              {item.id === 'alerts' && alertCount > 0 && (
                <span className={cn(
                  "absolute flex items-center justify-center bg-rose-500 text-[9px] font-bold text-white rounded-full transition-all",
                  isExpanded ? "right-3 w-5 h-4" : "-top-1 -right-1 w-4 h-4 shadow-glow-red/20"
                )}>
                  {alertCount > 9 ? '9+' : alertCount}
                </span>
              )}

              {/* Active Glow Bar */}
              {isActive && !isExpanded && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-sky-400 shadow-glow-blue" />
              )}
            </button>
          );

          if (isExpanded) return <div key={item.id}>{content}</div>;

          return (
            <Tooltip key={item.id} content={item.label} side="right">
              {content}
            </Tooltip>
          );
        })}
      </nav>

      {/* Footer / Toggle */}
      <div className="p-3 border-t border-slate-800/60 mt-auto">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full h-9 flex items-center justify-center rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-all"
        >
          {isExpanded ? (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="ml-2 text-xs font-medium">Collapse</span>
            </>
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
