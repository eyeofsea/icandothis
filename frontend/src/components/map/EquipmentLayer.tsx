'use client';

import { Equipment } from '@/lib/types';
import { CRITICALITY_COLORS } from '@/lib/constants';

// Rendering handled by MapInner via Leaflet API
export default function EquipmentLayer() {
  return null;
}

export function getEquipmentStyle(eq: Equipment) {
  const color = CRITICALITY_COLORS[eq.criticality] || '#22c55e';
  return { color, fillColor: color, fillOpacity: 1, weight: 2, radius: 5 };
}
