'use client';

import Modal from '@/components/ui/Modal';
import Badge from '@/components/ui/Badge';
import RiskBar from '@/components/ui/RiskBar';
import StatRow from '@/components/ui/StatRow';
import { useProjectStore } from '@/stores/projectStore';
import { Factory, MapPin, Award, Truck, Clock, Package, ShieldCheck, BarChart3 } from 'lucide-react';

interface SupplierDetailModalProps {
  supplierId: string | null;
  onClose: () => void;
}

export default function SupplierDetailModal({ supplierId, onClose }: SupplierDetailModalProps) {
  const { suppliers, equipment } = useProjectStore();
  const supplier = suppliers.find((s) => s.id === supplierId);

  if (!supplier) return null;

  const supplierEquip = equipment.filter((e) => e.supplierId === supplier.id);

  return (
    <Modal open={!!supplierId} onClose={onClose} title={supplier.name} width="max-w-xl">
      <div className="space-y-5">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="info">{supplier.category}</Badge>
          <Badge variant="default">{supplier.country}</Badge>
        </div>

        {/* Risk */}
        <div>
          <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Risk Score</span>
          <RiskBar score={supplier.riskScore} size="md" className="mt-1" />
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-3">
          <div className="glass-card p-3 rounded-lg text-center">
            <Award className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{supplier.qualityScore}%</div>
            <div className="text-[10px] text-slate-500">Quality Score</div>
          </div>
          <div className="glass-card p-3 rounded-lg text-center">
            <Truck className="w-4 h-4 text-green-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{supplier.onTimeDelivery}%</div>
            <div className="text-[10px] text-slate-500">On-Time Delivery</div>
          </div>
          <div className="glass-card p-3 rounded-lg text-center">
            <BarChart3 className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{supplier.capacity}%</div>
            <div className="text-[10px] text-slate-500">Capacity</div>
          </div>
        </div>

        {/* Stats */}
        <div className="glass-card p-3 rounded-lg">
          <StatRow icon={MapPin} label="Location" value={supplier.country} color="text-purple-400" />
          <StatRow icon={Factory} label="Category" value={supplier.category} />
          <StatRow icon={Clock} label="Lead Time" value={`${supplier.leadTimeDays} days`} color="text-orange-400" />
          <StatRow icon={Package} label="Active Orders" value={supplier.activeOrders} color="text-cyan-400" />
        </div>

        {/* Certifications */}
        <div>
          <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Certifications</span>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {supplier.certifications.map((cert) => (
              <div key={cert} className="flex items-center gap-1 px-2 py-1 glass-card rounded-md">
                <ShieldCheck className="w-3 h-3 text-green-400" />
                <span className="text-[10px] text-slate-300">{cert}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Equipment supplied */}
        {supplierEquip.length > 0 && (
          <div>
            <span className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">Equipment Supplied</span>
            <div className="mt-2 space-y-1.5">
              {supplierEquip.map((eq) => (
                <div key={eq.id} className="flex items-center justify-between py-2 px-3 glass-card rounded-lg">
                  <div className="text-xs font-medium text-white">{eq.name}</div>
                  <RiskBar score={eq.riskScore} className="w-20" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
