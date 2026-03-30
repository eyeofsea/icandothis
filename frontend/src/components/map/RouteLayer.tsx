'use client';

import { ShippingRoute } from '@/lib/types';
import { ROUTE_COLORS } from '@/lib/constants';

// Rendering is handled by MapInner via Leaflet API
// This module exports styling utilities for routes
export default function RouteLayer() {
  return null;
}

export function getRouteStyle(route: ShippingRoute) {
  const color = ROUTE_COLORS[route.status] || ROUTE_COLORS.active;
  const weight = Math.max(2, route.equipmentIds.length * 1.5);
  const dashArray = route.status === 'alternative' ? '10,6' : route.status === 'disrupted' ? '4,8' : undefined;
  return { color, weight, opacity: 0.8, dashArray };
}
