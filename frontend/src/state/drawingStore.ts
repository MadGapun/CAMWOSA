import { create } from "zustand";
import type { GeometrieObjekt } from "../api/types";

export type ZeichenWerkzeug =
  | "auswahl"
  | "linie"
  | "rechteck"
  | "kreis"
  | "polygon"
  | "punkt";

export interface ZeichenObjekt extends GeometrieObjekt {
  id: string;
}

interface DrawingState {
  werkzeug: ZeichenWerkzeug;
  setWerkzeug: (w: ZeichenWerkzeug) => void;

  objekte: ZeichenObjekt[];
  hinzufuegen: (o: ZeichenObjekt) => void;
  loeschen: (id: string) => void;
  alle_loeschen: () => void;
  ersetzen: (objekte: ZeichenObjekt[]) => void;

  ausgewaehlteId: string | null;
  setAusgewaehlt: (id: string | null) => void;

  snap_grid: number;
  setSnapGrid: (v: number) => void;
}

export const useDrawingStore = create<DrawingState>((set) => ({
  werkzeug: "auswahl",
  setWerkzeug: (w) => set({ werkzeug: w }),

  objekte: [],
  hinzufuegen: (o) => set((s) => ({ objekte: [...s.objekte, o] })),
  loeschen: (id) =>
    set((s) => ({
      objekte: s.objekte.filter((o) => o.id !== id),
      ausgewaehlteId: s.ausgewaehlteId === id ? null : s.ausgewaehlteId,
    })),
  alle_loeschen: () => set({ objekte: [], ausgewaehlteId: null }),
  ersetzen: (objekte) => set({ objekte }),

  ausgewaehlteId: null,
  setAusgewaehlt: (id) => set({ ausgewaehlteId: id }),

  snap_grid: 1,
  setSnapGrid: (v) => set({ snap_grid: v }),
}));

export function snap(v: number, grid: number): number {
  if (grid <= 0) return v;
  return Math.round(v / grid) * grid;
}

export function neuesObjekt(typ: GeometrieObjekt["typ"]): ZeichenObjekt {
  return {
    id: `obj_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    typ,
    layer: "Zeichnung",
    punkte: [],
    geschlossen: false,
    attribute: {},
  };
}
