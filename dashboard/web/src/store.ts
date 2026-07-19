import { create } from "zustand";
import type { HUMModel, FragmentType } from "./types";

export type ViewMode = "graph" | "flow" | "timeline";
export type MachineSel = "plato" | "hermes" | "both";

interface FilterState {
  types: Set<FragmentType>;
  trust: Set<string>;
  machine: MachineSel;
  status: Set<string>;
}

interface AppState {
  model: HUMModel | null;
  view: ViewMode;
  machine: MachineSel;
  selectedId: string | null;
  filter: FilterState;
  webgpu: boolean;
  hermesAvailable: boolean;
  pulling: boolean;
  lastError: string | null;
  commandOpen: boolean;

  setModel: (m: HUMModel) => void;
  setView: (v: ViewMode) => void;
  setMachine: (m: MachineSel) => void;
  select: (id: string | null) => void;
  toggleType: (t: FragmentType) => void;
  toggleTrust: (t: string) => void;
  toggleStatus: (s: string) => void;
  clearFilters: () => void;
  setWebGPU: (v: boolean) => void;
  setPulling: (v: boolean) => void;
  setHermesAvailable: (v: boolean) => void;
  setError: (e: string | null) => void;
  toggleCommand: (v?: boolean) => void;
}

const ALL_TYPES: FragmentType[] = [
  "OBSERVATION", "BEHAVIOUR", "ASSOCIATION", "QUESTION",
  "CONTRADICTION", "RESISTANCE", "SEED", "WARNING",
];

export const useStore = create<AppState>((set) => ({
  model: null,
  view: "graph",
  machine: "both",
  selectedId: null,
  filter: {
    types: new Set(ALL_TYPES),
    trust: new Set(),
    machine: "both",
    status: new Set(),
  },
  webgpu: false,
  hermesAvailable: false,
  pulling: false,
  lastError: null,
  commandOpen: false,

  setModel: (m) =>
    set({
      model: m,
      hermesAvailable: m.sources?.hermes_available ?? false,
    }),
  setView: (view) => set({ view }),
  setMachine: (machine) =>
    set((s) => ({ machine, filter: { ...s.filter, machine } })),
  select: (selectedId) => set({ selectedId }),
  toggleType: (t) =>
    set((s) => {
      const types = new Set(s.filter.types);
      types.has(t) ? types.delete(t) : types.add(t);
      return { filter: { ...s.filter, types } };
    }),
  toggleTrust: (t) =>
    set((s) => {
      const trust = new Set(s.filter.trust);
      trust.has(t) ? trust.delete(t) : trust.add(t);
      return { filter: { ...s.filter, trust } };
    }),
  toggleStatus: (st) =>
    set((s) => {
      const status = new Set(s.filter.status);
      status.has(st) ? status.delete(st) : status.add(st);
      return { filter: { ...s.filter, status } };
    }),
  clearFilters: () =>
    set((s) => ({
      filter: { types: new Set(ALL_TYPES), trust: new Set(), machine: s.machine, status: new Set() },
      selectedId: null,
    })),
  setWebGPU: (webgpu) => set({ webgpu }),
  setPulling: (pulling) => set({ pulling }),
  setHermesAvailable: (hermesAvailable) => set({ hermesAvailable }),
  setError: (lastError) => set({ lastError }),
  toggleCommand: (v) => set((s) => ({ commandOpen: v ?? !s.commandOpen })),
}));

export { ALL_TYPES };
