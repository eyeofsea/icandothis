'use client';

import {
  LayoutDashboard,
  ShieldAlert,
  FolderKanban,
  Bell,
  Globe,
  GitFork,
  Zap,
  FlaskConical,
  Radar,
} from 'lucide-react';
import Tooltip from '@/components/ui/Tooltip';
import { cn } from '@/lib/utils';

export type ViewId = 'dashboard' | 'riskmatrix' | 'projects' | 'alerts' | 'map' | 'ontology' | 'impact' | 'scenario';

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
  { id: 'map', label: 'Map', icon: Globe },
  { id: 'ontology', label: 'Ontology', icon: GitFork },
  { id: 'impact', label: 'Impact', icon: Zap },
  { id: 'scenario', label: 'Scenario', icon: FlaskConical },
];

interface SidebarProps {
  activeView: ViewId;
  onViewChange: (view: ViewId) => void;
  alertCount?: number;
}

export default function Sidebar({ activeView, onViewChange, alertCount = 0 }: SidebarProps) {
  return (
    <aside className="w-14 flex-shrink-0 bg-[#070b14] border-r border-[#1e3a5f]/60 flex flex-col items-center py-3 gap-1 z-[100]">
      {/* Logo */}
      <div className="mb-4 p-2">
        <Radar className="w-6 h-6 text-cyan-400" />
      </div>

      {/* Nav items */}
      <nav className="flex flex-col gap-1 flex-1">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <Tooltip key={item.id} content={item.label} side="right">
              <button
                onClick={() => onViewChange(item.id)}
                className={cn(
                  'relative w-10 h-10 flex items-center justify-center rounded-lg transition-all',
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                )}
              >
                <item.icon className="w-[18px] h-[18px]" />
                {item.id === 'alerts' && alertCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-[8px] text-white flex items-center justify-center font-bold">
                    {alertCount > 9 ? '9+' : alertCount}
                  </span>
                )}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-cyan-400" />
                )}
              </button>
            </Tooltip>
          );
        })}
      </nav>
    </aside>
  );
}
