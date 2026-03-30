import { create } from 'zustand';

interface VisibleLayers {
  projects: boolean;
  suppliers: boolean;
  routes: boolean;
  zones: boolean;
  equipment: boolean;
  disruptions: boolean;
  alternatives: boolean;
}

interface MapState {
  selectedProjectId: string | null;
  selectedEquipmentId: string | null;
  selectedSupplierId: string | null;
  activeDisruptionId: string | null;
  visibleLayers: VisibleLayers;
  mapCenter: [number, number];
  mapZoom: number;
  setSelectedProject: (id: string | null) => void;
  setSelectedEquipment: (id: string | null) => void;
  setSelectedSupplier: (id: string | null) => void;
  setActiveDisruption: (id: string | null) => void;
  toggleLayer: (layer: keyof VisibleLayers) => void;
  setMapCenter: (center: [number, number]) => void;
  setMapZoom: (zoom: number) => void;
}

export const useMapStore = create<MapState>((set) => ({
  selectedProjectId: null,
  selectedEquipmentId: null,
  selectedSupplierId: null,
  activeDisruptionId: null,
  visibleLayers: {
    projects: true,
    suppliers: true,
    routes: true,
    zones: true,
    equipment: true,
    disruptions: true,
    alternatives: false,
  },
  mapCenter: [25, 45],
  mapZoom: 3,
  setSelectedProject: (id) => set({ selectedProjectId: id }),
  setSelectedEquipment: (id) => set({ selectedEquipmentId: id }),
  setSelectedSupplier: (id) => set({ selectedSupplierId: id }),
  setActiveDisruption: (id) => set({ activeDisruptionId: id }),
  toggleLayer: (layer) =>
    set((state) => ({
      visibleLayers: {
        ...state.visibleLayers,
        [layer]: !state.visibleLayers[layer],
      },
    })),
  setMapCenter: (center) => set({ mapCenter: center }),
  setMapZoom: (zoom) => set({ mapZoom: zoom }),
}));
