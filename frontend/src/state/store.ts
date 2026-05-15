import { create } from "zustand";
import type { MaschinenProfil, Werkzeug, Material } from "../api/client";

interface AppState {
  backendOk: boolean;
  setBackendOk: (ok: boolean) => void;

  maschinen: MaschinenProfil[];
  werkzeuge: Werkzeug[];
  materialien: Material[];
  setStammdaten: (m: MaschinenProfil[], w: Werkzeug[], mat: Material[]) => void;

  aktiveMaschineId: string | null;
  setAktiveMaschine: (id: string | null) => void;

  aktivesProjekt: unknown | null;
  setAktivesProjekt: (p: unknown | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  backendOk: false,
  setBackendOk: (ok) => set({ backendOk: ok }),

  maschinen: [],
  werkzeuge: [],
  materialien: [],
  setStammdaten: (m, w, mat) =>
    set({ maschinen: m, werkzeuge: w, materialien: mat }),

  aktiveMaschineId: null,
  setAktiveMaschine: (id) => set({ aktiveMaschineId: id }),

  aktivesProjekt: null,
  setAktivesProjekt: (p) => set({ aktivesProjekt: p }),
}));
