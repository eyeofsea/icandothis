'use client';

import { Equipment } from '@/lib/types';
import { CRITICALITY_COLORS } from '@/lib/constants';

interface EquipmentLayerProps {
  equipment: Equipment[];
  onEquipmentClick?: (eq: Equipment) => void;
}

export default function EquipmentLayer({ equipment, onEquipmentClick }: EquipmentLayerProps) {
  // Rendering handled by MapInner via Leaflet API directly
  return null;
}

export function getEquipmentStyle(eq: Equipment) {
  const color = CRITICALITY_COLORS[eq.criticality] || '#22c55e';
  return { color, fillColor: color, fillOpacity: 1, weight: 2, radius: 5 };
}
