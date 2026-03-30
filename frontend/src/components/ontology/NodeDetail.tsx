'use client';

import { GraphNode } from '@/lib/types';
import { NODE_COLORS } from '@/lib/constants';
import { X, Search, BarChart3 } from 'lucide-react';

interface NodeDetailProps {
  node: GraphNode;
  onClose: () => void;
}

export default function NodeDetail({ node, onClose }: NodeDetailProps) {
  const color = NODE_COLORS[node.type] || '#6b7280';
  const data = node.data as Record<string, unknown>;

  const displayFields = Object.entries(data).filter(
    ([key]) => !['id', 'boundaries', 'waypoints', 'equipmentIds', 'location', 'currentPosition'].includes(key)
  );

  return (
    <div className="p-3">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ background: color }} />
          <span className="text-[10px] font-semibold text-slate-400 uppercase">{node.type}</span>
        </div>
        <button onClick={onClose} className="p-0.5 hover:bg-white/10 rounded">
          <X className="w-3 h-3 text-slate-500" />
        </button>
      </div>

      <h3 className="text-xs font-bold text-white mb-3 leading-tight">{node.label}</h3>

      <div className="space-y-1.5 mb-4">
        {displayFields.map(([key, value]) => (
          <div key={key} className="flex justify-between text-[9px]">
            <span className="text-slate-500 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
            <span className="text-slate-300 text-right max-w-[80px] truncate">
              {Array.isArray(value) ? `${(value as unknown[]).length} items` : String(value)}
            </span>
          </div>
        ))}
      </div>

      <div className="space-y-1.5 border-t border-[#1e3a5f] pt-3">
        <button className="w-full flex items-center gap-1.5 text-[9px] text-cyan-400 hover:text-cyan-300 py-1">
          <Search className="w-3 h-3" />
          Find Alternatives
        </button>
        <button className="w-full flex items-center gap-1.5 text-[9px] text-orange-400 hover:text-orange-300 py-1">
          <BarChart3 className="w-3 h-3" />
          Analyze Impact
        </button>
      </div>
    </div>
  );
}
