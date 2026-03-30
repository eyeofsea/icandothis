'use client';

import { Supplier } from '@/lib/types';
import { CATEGORY_COLORS } from '@/lib/constants';

// Rendering handled by MapInner via Leaflet API
export default function SupplierLayer() {
  return null;
}

export function getSupplierStyle(supplier: Supplier) {
  const color = CATEGORY_COLORS[supplier.category] || '#3b82f6';
  const radius = Math.max(6, Math.min(12, supplier.capacity / 10));
  return { color, radius, fillColor: color, fillOpacity: 0.7, weight: 2 };
}
