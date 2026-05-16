import { create } from "zustand";
import type {
  CheckBericht,
  GeometrieObjekt,
  MaschinenProfil,
  Material,
  OperationEintrag,
  Spindel,
  Werkzeug,
} from "../api/types";

interface AppState {
  // Backend-Verbindung
  backendOk: boolean;
  setBackendOk: (ok: boolean) => void;

  // Stammdaten
  maschinen: MaschinenProfil[];
  werkzeuge: Werkzeug[];
  materialien: Material[];
  spindeln: Spindel[];
  setStammdaten: (
    m: MaschinenProfil[], w: Werkzeug[], mat: Material[], sp: Spindel[],
  ) => void;

  // Aktive Auswahl
  aktiveMaschineId: string | null;
  setAktiveMaschine: (id: string | null) => void;

  /** Override fuer aktive Spindel — sonst Default aus Maschine. */
  aktiveSpindelId: string | null;
  setAktiveSpindelId: (id: string | null) => void;

  aktivesMaterialId: string | null;
  setAktivesMaterial: (id: string | null) => void;

  // Geometrien (importiert aus DXF oder gezeichnet)
  geometrien: GeometrieObjekt[];
  setGeometrien: (g: GeometrieObjekt[]) => void;
  geometrieHinzufuegen: (g: GeometrieObjekt) => void;
  geometrienLeeren: () => void;
  ausgewaehlteGeometrieIndex: number | null;
  setAusgewaehlteGeometrieIndex: (i: number | null) => void;

  // Operationen
  operationen: OperationEintrag[];
  operationHinzufuegen: (op: OperationEintrag) => void;
  operationAktualisieren: (id: string, patch: Partial<OperationEintrag>) => void;
  operationLoeschen: (id: string) => void;
  operationenLeeren: () => void;
  aktiveOperationId: string | null;
  setAktiveOperationId: (id: string | null) => void;

  // Sicherheits-Bericht (aktuell angezeigter)
  aktuellerSicherheitsbericht: CheckBericht | null;
  setSicherheitsbericht: (b: CheckBericht | null) => void;
  ausgewaehltesSicherheitsergebnisIndex: number | null;
  setAusgewaehltesSicherheitsergebnis: (i: number | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  backendOk: false,
  setBackendOk: (ok) => set({ backendOk: ok }),

  maschinen: [],
  werkzeuge: [],
  materialien: [],
  spindeln: [],
  setStammdaten: (m, w, mat, sp) =>
    set({ maschinen: m, werkzeuge: w, materialien: mat, spindeln: sp }),

  aktiveSpindelId: null,
  setAktiveSpindelId: (id) => set({ aktiveSpindelId: id }),

  aktiveMaschineId: null,
  setAktiveMaschine: (id) => set({ aktiveMaschineId: id }),

  aktivesMaterialId: null,
  setAktivesMaterial: (id) => set({ aktivesMaterialId: id }),

  geometrien: [],
  setGeometrien: (g) => set({ geometrien: g }),
  geometrieHinzufuegen: (g) => set((s) => ({ geometrien: [...s.geometrien, g] })),
  geometrienLeeren: () => set({ geometrien: [] }),
  ausgewaehlteGeometrieIndex: null,
  setAusgewaehlteGeometrieIndex: (i) => set({ ausgewaehlteGeometrieIndex: i }),

  operationen: [],
  operationHinzufuegen: (op) => set((s) => ({ operationen: [...s.operationen, op] })),
  operationAktualisieren: (id, patch) =>
    set((s) => ({
      operationen: s.operationen.map((op) =>
        op.id === id ? { ...op, ...patch } : op,
      ),
    })),
  operationLoeschen: (id) =>
    set((s) => ({
      operationen: s.operationen.filter((op) => op.id !== id),
      aktiveOperationId: s.aktiveOperationId === id ? null : s.aktiveOperationId,
    })),
  operationenLeeren: () => set({ operationen: [], aktiveOperationId: null }),
  aktiveOperationId: null,
  setAktiveOperationId: (id) => set({ aktiveOperationId: id }),

  aktuellerSicherheitsbericht: null,
  setSicherheitsbericht: (b) => set({ aktuellerSicherheitsbericht: b }),
  ausgewaehltesSicherheitsergebnisIndex: null,
  setAusgewaehltesSicherheitsergebnis: (i) =>
    set({ ausgewaehltesSicherheitsergebnisIndex: i }),
}));

// Selektoren fuer abgeleitete Werte
export const useAktiveMaschine = () =>
  useAppStore((s) => s.maschinen.find((m) => m.id === s.aktiveMaschineId) ?? null);

/**
 * Effektive aktive Spindel:
 * 1. Wenn explizit per `aktiveSpindelId` gesetzt -> diese
 * 2. Sonst: aktive_spindel_id der aktiven Maschine
 * 3. Sonst: null
 */
export const useAktiveSpindel = () =>
  useAppStore((s) => {
    const maschine = s.maschinen.find((m) => m.id === s.aktiveMaschineId);
    const id = s.aktiveSpindelId ?? maschine?.aktive_spindel_id ?? null;
    return s.spindeln.find((sp) => sp.id === id) ?? null;
  });

export const useAktivesMaterial = () =>
  useAppStore((s) => s.materialien.find((m) => m.id === s.aktivesMaterialId) ?? null);

export const useAktiveOperation = () =>
  useAppStore((s) => s.operationen.find((op) => op.id === s.aktiveOperationId) ?? null);
