'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { MAP_CONFIG, CATEGORY_COLORS, CRITICALITY_COLORS, ROUTE_COLORS, ZONE_RISK_COLORS } from '@/lib/constants';
import { useMapStore } from '@/stores/mapStore';
import { useProjectStore } from '@/stores/projectStore';
import { useDisruptionStore } from '@/stores/disruptionStore';
import { useMapLayers } from '@/hooks/useMapLayers';
import { formatCurrency } from '@/lib/utils';
import MapLegend from './MapLegend';

export default function MapInner() {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.LayerGroup[]>([]);

  const { setSelectedProject, setSelectedEquipment, setSelectedSupplier } = useMapStore();
  const { projects } = useProjectStore();
  const { activeDisruptions } = useDisruptionStore();
  const {
    filteredProjects,
    filteredSuppliers,
    filteredRoutes,
    filteredEquipment,
    filteredZones,
    filteredDisruptions,
  } = useMapLayers();

  // Initialize map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: MAP_CONFIG.center,
      zoom: MAP_CONFIG.zoom,
      minZoom: MAP_CONFIG.minZoom,
      maxZoom: MAP_CONFIG.maxZoom,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer(MAP_CONFIG.tileUrl, {
      attribution: MAP_CONFIG.tileAttribution,
      maxZoom: 19,
    }).addTo(map);

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Clear old layers
    layersRef.current.forEach((lg) => lg.clearLayers());
    layersRef.current = [];

    // Zone layer
    const zoneGroup = L.layerGroup().addTo(map);
    filteredZones.forEach((zone) => {
      if (zone.boundaries.length > 2) {
        const color = ZONE_RISK_COLORS[zone.riskLevel] || ZONE_RISK_COLORS.low;
        const borderColor = zone.riskLevel === 'critical' ? '#ef4444' : zone.riskLevel === 'high' ? '#f97316' : zone.riskLevel === 'medium' ? '#eab308' : '#22c55e';
        L.polygon(
          zone.boundaries.map((b) => [b.lat, b.lng] as L.LatLngTuple),
          { color: borderColor, weight: 1, fillColor: color, fillOpacity: 0.3, dashArray: '5,5' }
        )
          .bindPopup(`<div style="min-width:180px"><strong>${zone.name}</strong><br/><span style="color:${borderColor}">Risk: ${zone.riskLevel.toUpperCase()}</span><br/><small>${zone.description}</small><br/><small>Threats: ${zone.activeThreats.join(', ')}</small></div>`)
          .addTo(zoneGroup);
      }
    });
    layersRef.current.push(zoneGroup);

    // Route layer
    const routeGroup = L.layerGroup().addTo(map);
    filteredRoutes.forEach((route) => {
      const points: L.LatLngTuple[] = [
        [route.origin.lat, route.origin.lng],
        ...route.waypoints.map((w) => [w.lat, w.lng] as L.LatLngTuple),
        [route.destination.lat, route.destination.lng],
      ];
      const color = ROUTE_COLORS[route.status] || ROUTE_COLORS.active;
      const weight = Math.max(2, route.equipmentIds.length * 1.5);
      const dashArray = route.status === 'alternative' ? '10,6' : route.status === 'disrupted' ? '4,8' : undefined;

      L.polyline(points, { color, weight, opacity: 0.8, dashArray })
        .bindPopup(`<div style="min-width:200px"><strong>${route.name}</strong><br/>Status: <span style="color:${color}">${route.status}</span><br/>Distance: ${route.distanceNm.toLocaleString()} nm<br/>Transit: ${route.transitDays} days<br/>Equipment: ${route.equipmentIds.length} items<br/>Cost: $${route.costPerTon}/ton<br/>Risk: ${route.riskScore}/100</div>`)
        .addTo(routeGroup);

      // Origin marker
      L.circleMarker([route.origin.lat, route.origin.lng], { radius: 4, color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 1, weight: 1 })
        .bindTooltip(route.origin.port, { className: 'leaflet-tooltip', direction: 'top' })
        .addTo(routeGroup);
      // Dest marker
      L.circleMarker([route.destination.lat, route.destination.lng], { radius: 4, color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 1, weight: 1 })
        .bindTooltip(route.destination.port, { className: 'leaflet-tooltip', direction: 'top' })
        .addTo(routeGroup);
    });
    layersRef.current.push(routeGroup);

    // Supplier layer
    const supplierGroup = L.layerGroup().addTo(map);
    filteredSuppliers.forEach((supplier) => {
      const color = CATEGORY_COLORS[supplier.category] || '#3b82f6';
      const radius = Math.max(6, Math.min(12, supplier.capacity / 10));
      L.circleMarker([supplier.location.lat, supplier.location.lng], {
        radius,
        color,
        fillColor: color,
        fillOpacity: 0.7,
        weight: 2,
      })
        .bindPopup(`<div style="min-width:220px"><strong>${supplier.name}</strong><br/>${supplier.country}<br/>Category: ${supplier.category}<br/>Quality: ${supplier.qualityScore}%<br/>On-Time: ${supplier.onTimeDelivery}%<br/>Capacity: ${supplier.capacity}%<br/>Active Orders: ${supplier.activeOrders}<br/>Risk Score: ${supplier.riskScore}/100<br/>Lead Time: ${supplier.leadTimeDays} days<br/><small>${supplier.certifications.join(', ')}</small></div>`)
        .on('click', () => setSelectedSupplier(supplier.id))
        .addTo(supplierGroup);
    });
    layersRef.current.push(supplierGroup);

    // Project layer
    const projectGroup = L.layerGroup().addTo(map);
    filteredProjects.forEach((proj) => {
      const statusColor = proj.status === 'on-track' ? '#22c55e' : proj.status === 'at-risk' ? '#eab308' : proj.status === 'delayed' ? '#f97316' : '#ef4444';
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:20px;height:20px;background:${statusColor};border:2px solid white;border-radius:4px;transform:rotate(45deg);box-shadow:0 0 8px ${statusColor}80;"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });
      L.marker([proj.location.lat, proj.location.lng], { icon })
        .bindPopup(`<div style="min-width:220px"><strong>${proj.name}</strong><br/>Client: ${proj.client}<br/>Value: ${formatCurrency(proj.value)}<br/>Progress: ${proj.completionPercent}%<br/>Status: <span style="color:${statusColor}">${proj.status}</span><br/>Equipment: ${proj.equipmentIds.length} items</div>`)
        .on('click', () => setSelectedProject(proj.id))
        .addTo(projectGroup);
    });
    layersRef.current.push(projectGroup);

    // Equipment in transit
    const equipGroup = L.layerGroup().addTo(map);
    filteredEquipment.forEach((eq) => {
      if (!eq.currentPosition) return;
      const color = CRITICALITY_COLORS[eq.criticality] || '#22c55e';
      const icon = L.divIcon({
        className: '',
        html: `<div style="width:10px;height:10px;background:${color};border:2px solid white;border-radius:50%;box-shadow:0 0 6px ${color}80;"></div>`,
        iconSize: [10, 10],
        iconAnchor: [5, 5],
      });
      L.marker([eq.currentPosition.lat, eq.currentPosition.lng], { icon })
        .bindPopup(`<div style="min-width:200px"><strong>${eq.name}</strong><br/>Type: ${eq.type}<br/>Criticality: <span style="color:${color}">${eq.criticality}</span><br/>Status: ${eq.status}<br/>Value: ${formatCurrency(eq.value)}<br/>Risk: ${eq.riskScore}/100</div>`)
        .on('click', () => setSelectedEquipment(eq.id))
        .addTo(equipGroup);
    });
    layersRef.current.push(equipGroup);

    // Disruption layer
    const disruptionGroup = L.layerGroup().addTo(map);
    filteredDisruptions.forEach((d) => {
      const opacity = Math.min(0.6, d.severity * 0.12);
      L.circle([d.location.lat, d.location.lng], {
        radius: d.radius * 1000,
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: opacity,
        weight: 2,
        dashArray: '4,4',
      })
        .bindPopup(`<div style="min-width:200px"><strong>${d.name}</strong><br/>Type: ${d.type}<br/>Severity: ${'*'.repeat(d.severity)}<br/>${d.description}<br/>Affected Routes: ${d.affectedRouteIds.length}<br/>Affected Equipment: ${d.affectedEquipmentIds.length}</div>`)
        .addTo(disruptionGroup);
    });
    layersRef.current.push(disruptionGroup);
  }, [filteredProjects, filteredSuppliers, filteredRoutes, filteredEquipment, filteredZones, filteredDisruptions, projects, activeDisruptions, setSelectedProject, setSelectedEquipment, setSelectedSupplier]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      <MapLegend />
    </div>
  );
}
