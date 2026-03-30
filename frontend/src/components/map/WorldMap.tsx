'use client';

import dynamic from 'next/dynamic';

const MapInner = dynamic(() => import('./MapInner'), { ssr: false });

export default function WorldMap() {
  return (
    <div className="w-full h-full relative">
      <MapInner />
    </div>
  );
}
