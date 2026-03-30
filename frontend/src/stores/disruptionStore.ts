import { create } from 'zustand';
import { DisruptionEvent, ImpactAnalysis, SupplierRecommendation, RouteAlternative } from '@/lib/types';

interface DisruptionState {
  activeDisruptions: DisruptionEvent[];
  affectedEquipmentIds: string[];
  affectedRouteIds: string[];
  impactAnalysis: ImpactAnalysis | null;
  recommendations: SupplierRecommendation[];
  routeAlternatives: RouteAlternative[];
  addDisruption: (d: DisruptionEvent) => void;
  removeDisruption: (id: string) => void;
  setImpactAnalysis: (analysis: ImpactAnalysis | null) => void;
  setRecommendations: (recs: SupplierRecommendation[]) => void;
  setRouteAlternatives: (alts: RouteAlternative[]) => void;
  clearDisruptions: () => void;
}

export const useDisruptionStore = create<DisruptionState>((set) => ({
  activeDisruptions: [],
  affectedEquipmentIds: [],
  affectedRouteIds: [],
  impactAnalysis: null,
  recommendations: [],
  routeAlternatives: [],
  addDisruption: (d) =>
    set((state) => ({
      activeDisruptions: [...state.activeDisruptions, d],
      affectedEquipmentIds: Array.from(
        new Set([...state.affectedEquipmentIds, ...d.affectedEquipmentIds])
      ),
      affectedRouteIds: Array.from(
        new Set([...state.affectedRouteIds, ...d.affectedRouteIds])
      ),
    })),
  removeDisruption: (id) =>
    set((state) => ({
      activeDisruptions: state.activeDisruptions.filter((d) => d.id !== id),
    })),
  setImpactAnalysis: (analysis) => set({ impactAnalysis: analysis }),
  setRecommendations: (recs) => set({ recommendations: recs }),
  setRouteAlternatives: (alts) => set({ routeAlternatives: alts }),
  clearDisruptions: () =>
    set({
      activeDisruptions: [],
      affectedEquipmentIds: [],
      affectedRouteIds: [],
      impactAnalysis: null,
      recommendations: [],
      routeAlternatives: [],
    }),
}));
