'use client';

import { ShippingRoute } from '@/lib/types';
import { ROUTE_COLORS } from '@/lib/constants';

interface RouteLayerProps {
  routes: ShippingRoute[];
  onRouteClick?: (route: ShippingRoute) => void;
}

export default function RouteLayer({ routes, onRouteClick }: RouteLayerProps) {
  // This component is used as a reference — actual rendering is done in MapInner via Leaflet API
  // Keeping as a logical component for potential future React-Leaflet migration
  return null;
}

export function getRouteStyle(route: ShippingRoute) {
  const color = ROUTE_COLORS[route.status] || ROUTE_COLORS.active;
  const weight = Math.max(2, route.equipmentIds.length * 1.5);
  const dashArray = route.status === 'alternative' ? '10,6' : route.status === 'disrupted' ? '4,8' : undefined;
  return { color, weight, opacity: 0.8, dashArray };
}
