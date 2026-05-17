import { create } from "zustand";

/**
 * Projekt-Metadaten + Speicher-Zustand (Master-Plan D4).
 *
 * Haelt rein die Metadaten — die eigentlichen Daten leben in:
 * - useAppStore (Geometrien, Operationen)
 * - useWorkflowStore (Setups)
 * - useRohmaterialStore (Rohmaterial)
 * - useVarianteStore (Varianten-Snapshots)
 */
interface ProjektState {
  /** Aktueller Dateiname. Leerstring = unbenanntes Projekt. */
  dateiname: string;
  setDateiname: (name: string) => void;

  /** Autor (wird beim Speichern in metadaten geschrieben). */
  autor: string;
  setAutor: (autor: string) => void;

  /** Wurde seit dem letzten Speichern etwas geaendert? */
  dirty: boolean;
  setDirty: (d: boolean) => void;

  /** Zuletzt geoeffnete Projekt-Pfade (lokal in localStorage). */
  zuletzt_geoeffnet: string[];
  zuletztHinzufuegen: (pfad: string) => void;
}

const STORAGE_KEY = "camwosa.zuletzt_geoeffnet";

function _ladeZuletzt(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}

function _speichereZuletzt(liste: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(liste));
  } catch {
    // Quota voll oder Storage geblockt — ignorieren
  }
}

export const useProjektStore = create<ProjektState>((set) => ({
  dateiname: "",
  setDateiname: (name) => set({ dateiname: name }),

  autor: "",
  setAutor: (autor) => set({ autor }),

  dirty: false,
  setDirty: (d) => set({ dirty: d }),

  zuletzt_geoeffnet: _ladeZuletzt(),
  zuletztHinzufuegen: (pfad) => {
    set((s) => {
      const ohne = s.zuletzt_geoeffnet.filter((p) => p !== pfad);
      const neu = [pfad, ...ohne].slice(0, 8);
      _speichereZuletzt(neu);
      return { zuletzt_geoeffnet: neu };
    });
  },
}));
