import { create } from "zustand";

export type RohmaterialForm = "quader" | "zylinder" | "platte" | "frei";
export type NullpunktReferenz = "material_top" | "material_bottom" | "tisch_top";

export interface Rohmaterial {
  form: RohmaterialForm;
  laenge: number;
  breite: number;
  hoehe: number;
  material_id: string;
  nullpunkt: [number, number, number];
  z_referenz: NullpunktReferenz;
  rotation_grad: number;
}

interface State {
  rohmaterial: Rohmaterial;
  setze: (r: Partial<Rohmaterial>) => void;
  reset: () => void;
}

const DEFAULT: Rohmaterial = {
  form: "platte",
  laenge: 300,
  breite: 200,
  hoehe: 18,
  material_id: "buche_massiv",
  nullpunkt: [0, 0, 0],
  z_referenz: "material_top",
  rotation_grad: 0,
};

export const useRohmaterialStore = create<State>((set) => ({
  rohmaterial: DEFAULT,
  setze: (r) => set((s) => ({ rohmaterial: { ...s.rohmaterial, ...r } })),
  reset: () => set({ rohmaterial: DEFAULT }),
}));
