'use client';

import ImpactFlow from '@/components/impact/ImpactFlow';
import SupplierComparison from '@/components/impact/SupplierComparison';
import RouteComparison from '@/components/impact/RouteComparison';
import CostAnalysis from '@/components/impact/CostAnalysis';

export default function ImpactView() {
  return (
    <div className="h-full overflow-y-auto p-5">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-white">Impact Analysis</h2>
        <p className="text-xs text-slate-500 mt-0.5">Disruption cascade analysis and mitigation options</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="glass-card p-4 rounded-lg col-span-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Cascade Flow</span>
          <ImpactFlow />
        </div>
        <div className="glass-card p-4 rounded-lg">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Supplier Alternatives</span>
          <SupplierComparison />
        </div>
        <div className="glass-card p-4 rounded-lg">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Route Alternatives</span>
          <RouteComparison />
        </div>
        <div className="glass-card p-4 rounded-lg col-span-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">Cost Analysis</span>
          <CostAnalysis />
        </div>
      </div>
    </div>
  );
}
