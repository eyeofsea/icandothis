'use client';

import { DisruptionEvent } from '@/lib/types';

interface DisruptionLayerProps {
  disruptions: DisruptionEvent[];
  onDisruptionClick?: (disruption: DisruptionEvent) => void;
}

export default function DisruptionLayer({ disruptions, onDisruptionClick }: DisruptionLayerProps) {
  // Rendering handled by MapInner via Leaflet API directly
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
