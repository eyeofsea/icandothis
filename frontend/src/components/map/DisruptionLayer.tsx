'use client';

import { DisruptionEvent } from '@/lib/types';

// Rendering handled by MapInner via Leaflet API
export default function DisruptionLayer() {
  return null;
}

export function getDisruptionStyle(disruption: DisruptionEvent) {
  const opacity = Math.min(0.6, disruption.severity * 0.12);
  return {
    color: '#ef4444',
    fillColor: '#ef4444',
    fillOpacity: opacity,
    weight: 2,
    dashArray: '4,4',
    radius: disruption.radius * 1000,
  };
}
