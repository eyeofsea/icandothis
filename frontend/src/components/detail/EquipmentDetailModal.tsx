'use client';

import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import RiskBar from '@/components/ui/RiskBar';
import StatRow from '@/components/ui/StatRow';
import { useProjectStore } from '@/stores/projectStore';
import { formatCurrency } from '@/lib/utils';
import { Package, MapPin, Truck, Calendar, Weight, Factory, Shield, Clock } from 'lucide-react';

interface EquipmentDetailModalProps {
  equipmentId: string | null;
  onClose: () => void;
}

const criticalityVariant = (c: string) => {
  switch (c) {
    case 'Critical': return 'critical' as const;
    case 'High': return 'high' as const;
    case 'Medium': return 'medium' as const;
    default: return 'low' as const;
  }
};

const statusVariant = (s: string) => {
  switch (s) {
    case 'delayed': return 'critical' as const;
    case 'in-transit': return 'info' as const;
    case 'ready': return 'success' as const;
    case 'delivered': return 'success' as const;
    default: return 'default' as const;
  }
};

export default function EquipmentDetailModal({ equipmentId, onClose }: EquipmentDetailModalProps) {
  const { equipment, projects, suppliers, routes } = useProjectStore();
  const eq = equipment.find((e) => e.id === equipmentId);

  if (!eq) return null;

  const project = projects.find((p) => p.id === eq.projectId);
  const supplier = suppliers.find((s) => s.id === eq.supplierId);
  const route = routes.find((r) => r.id === eq.routeId);

  return (
    <Modal open={!!equipmentId} onClose={onClose} title={eq.name} width="max-w-xl">
      <div className="space-y-5">
        {/* Header badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={criticalityVariant(eq.criticality)}>{eq.criticality}</Badge>
          <Badge variant={statusVariant(eq.status)}>{eq.status}</Badge>
          <Badge variant="info">{eq.category}</Badge>
        </div>

        {/* Risk */}
        <div>
          <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Risk Score</span>
          <RiskBar score={eq.riskScore} size="md" className="mt-1" />
        </div>

        {/* Stats */}
        <div className="glass-card p-3 rounded-lg">
          <StatRow icon={Package} label="Type" value={eq.type} />
          <StatRow icon={Shield} label="Value" value={formatCurrency(eq.value)} color="text-green-400" />
          <StatRow icon={Weight} label="Weight" value={`${eq.weight} tons`} color="text-orange-400" />
          <StatRow icon={Calendar} label="Delivery Date" value={eq.deliveryDate} color="text-yellow-400" />
          <StatRow icon={Clock} label="Lead Time" value={`${eq.leadTimeDays} days`} />
          {eq.currentPosition && (
            <StatRow icon={MapPin} label="Current Position" value={`${eq.currentPosition.lat.toFixed(1)}°N, ${eq.currentPosition.lng.toFixed(1)}°E`} color="text-purple-400" />
          )}
        </div>

        {/* Related entities */}
        <div className="grid grid-cols-2 gap-3">
          {project && (
            <div className="glass-card p-3 rounded-lg">
              <div className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider mb-2">Project</div>
              <div className="text-sm font-medium text-white">{project.name}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{project.client}</div>
            </div>
          )}
          {supplier && (
            <div className="glass-card p-3 rounded-lg">
              <div className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider mb-2">Supplier</div>
              <div className="text-sm font-medium text-white">{supplier.name}</div>
              <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                <Factory className="w-3 h-3" /> {supplier.country}
              </div>
            </div>
          )}
        </div>

        {/* Route */}
        {route && (
          <div className="glass-card p-3 rounded-lg">
            <div className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider mb-2">Shipping Route</div>
            <div className="flex items-center gap-2">
              <Truck className="w-4 h-4 text-cyan-400" />
              <span className="text-sm text-white">{route.name}</span>
            </div>
            <div className="flex gap-4 mt-2 text-[10px] text-slate-400">
              <span>{route.distanceNm} NM</span>
              <span>{route.transitDays} days transit</span>
              <span>${route.costPerTon}/ton</span>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
