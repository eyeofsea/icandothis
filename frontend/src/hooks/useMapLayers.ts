'use client';

import { useMemo } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { useMapStore } from '@/stores/mapStore';
import { useDisruptionStore } from '@/stores/disruptionStore';

export function useMapLayers() {
  const { projects, equipment, suppliers, routes, zones } = useProjectStore();
  const { visibleLayers, selectedProjectId } = useMapStore();
  const { activeDisruptions, affectedRouteIds } = useDisruptionStore();

  const filteredProjects = useMemo(() => {
    if (!visibleLayers.projects) return [];
    return projects;
  }, [projects, visibleLayers.projects]);

  const filteredSuppliers = useMemo(() => {
    if (!visibleLayers.suppliers) return [];
    if (selectedProjectId) {
      const projEquipment = equipment.filter((e) => e.projectId === selectedProjectId);
      const supplierIds = new Set(projEquipment.map((e) => e.supplierId));
      return suppliers.filter((s) => supplierIds.has(s.id));
    }
    return suppliers;
  }, [suppliers, equipment, visibleLayers.suppliers, selectedProjectId]);

  const filteredRoutes = useMemo(() => {
    if (!visibleLayers.routes) return [];
    const disrupted = routes.map((r) => ({
      ...r,
      status: affectedRouteIds.includes(r.id) ? ('disrupted' as const) : r.status,
    }));
    if (selectedProjectId) {
      const projEquipment = equipment.filter((e) => e.projectId === selectedProjectId);
      const routeIds = new Set(projEquipment.map((e) => e.routeId));
      return disrupted.filter((r) => routeIds.has(r.id));
    }
    return disrupted;
  }, [routes, equipment, visibleLayers.routes, selectedProjectId, affectedRouteIds]);

  const filteredEquipment = useMemo(() => {
    if (!visibleLayers.equipment) return [];
    if (selectedProjectId) {
      return equipment.filter((e) => e.projectId === selectedProjectId);
    }
    return equipment.filter((e) => e.currentPosition);
  }, [equipment, visibleLayers.equipment, selectedProjectId]);

  const filteredZones = useMemo(() => {
    if (!visibleLayers.zones) return [];
    return zones;
  }, [zones, visibleLayers.zones]);

  const filteredDisruptions = useMemo(() => {
    if (!visibleLayers.disruptions) return [];
    return activeDisruptions;
  }, [activeDisruptions, visibleLayers.disruptions]);

  return {
    filteredProjects,
    filteredSuppliers,
    filteredRoutes,
    filteredEquipment,
    filteredZones,
    filteredDisruptions,
  };
}
