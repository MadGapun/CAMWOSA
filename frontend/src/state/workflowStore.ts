import { create } from "zustand";

// Spiegel zu backend/camwosa/project/schema.py (Setup, SetupPause, Variante).

export type SetupPauseTyp =
  | "werkzeugwechsel"
  | "umspann"
  | "werkstueck_verschieben"
  | "spindel_wechsel"
  | "optionaler_stop";

export interface SetupPause {
  typ: SetupPauseTyp;
  titel: string;
  anweisung: string;
  foto_pfad?: string | null;
  werkzeug_neu_id?: string | null;
  nullpunkt_neu?: [number, number, number] | null;
  bestaetigung_text?: string;
}

export type MaschinenModus = "standard_xyz" | "rotary_y" | "rotary_x" | "laser" | "drag_knife";

export interface Setup {
  id: string;
  name: string;
  maschinen_modus: MaschinenModus;
  spannmittel: string;
  werkzeug_id: string;
  rohmaterial_uebernehmen: boolean;
  nullpunkt: [number, number, number];
  operationen: unknown[];
  pause_vor: SetupPause | null;
  foto_pfad: string | null;
  geschaetzte_zeit_minuten: number;
  notizen: string;
}

interface WorkflowState {
  setups: Setup[];
  hinzufuegen: (s: Setup) => void;
  aktualisieren: (id: string, patch: Partial<Setup>) => void;
  loeschen: (id: string) => void;
  verschieben: (id: string, richtung: -1 | 1) => void;
  pauseSetzen: (setup_id: string, pause: SetupPause | null) => void;

  // Arbeitsplan-Checkliste — Status pro Setup oder Pause
  erledigt: Record<string, boolean>;
  toggleErledigt: (key: string) => void;
  alleZuruecksetzen: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  setups: [],
  hinzufuegen: (s) => set((state) => ({ setups: [...state.setups, s] })),
  aktualisieren: (id, patch) =>
    set((state) => ({
      setups: state.setups.map((s) => (s.id === id ? { ...s, ...patch } : s)),
    })),
  loeschen: (id) =>
    set((state) => ({ setups: state.setups.filter((s) => s.id !== id) })),
  verschieben: (id, richtung) =>
    set((state) => {
      const idx = state.setups.findIndex((s) => s.id === id);
      if (idx < 0) return state;
      const next = idx + richtung;
      if (next < 0 || next >= state.setups.length) return state;
      const arr = [...state.setups];
      [arr[idx], arr[next]] = [arr[next], arr[idx]];
      return { setups: arr };
    }),
  pauseSetzen: (setup_id, pause) =>
    set((state) => ({
      setups: state.setups.map((s) =>
        s.id === setup_id ? { ...s, pause_vor: pause } : s,
      ),
    })),

  erledigt: {},
  toggleErledigt: (key) =>
    set((state) => ({
      erledigt: { ...state.erledigt, [key]: !state.erledigt[key] },
    })),
  alleZuruecksetzen: () => set({ erledigt: {} }),
}));

export function neueSetup(name: string, werkzeug_id: string): Setup {
  return {
    id: `setup_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    name,
    maschinen_modus: "standard_xyz",
    spannmittel: "",
    werkzeug_id,
    rohmaterial_uebernehmen: true,
    nullpunkt: [0, 0, 0],
    operationen: [],
    pause_vor: null,
    foto_pfad: null,
    geschaetzte_zeit_minuten: 0,
    notizen: "",
  };
}
