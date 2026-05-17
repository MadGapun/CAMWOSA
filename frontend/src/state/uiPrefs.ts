/** UI-Preferences (Theme, Dichte, Vorschau-Modus) mit LocalStorage-Persistierung. */
import { create } from "zustand";

export type Theme = "dark" | "light";
export type Density = "compact" | "medium" | "comfortable";
export type VorschauModus = "aus" | "vereinfacht" | "komplett";

interface UIPrefsState {
  theme: Theme;
  density: Density;
  /** Globaler Default — pro Operation kann override gesetzt werden. */
  vorschauModusDefault: VorschauModus;

  /** Sichtbarkeit der App-Chrome — fuer maximale Arbeitsflaeche. */
  sidebarSichtbar: boolean;
  topbarSichtbar: boolean;
  statusbarSichtbar: boolean;
  /** Vollbild-Fokus — blendet alle 3 Leisten auf einmal aus.
   * Wird NICHT persistiert (Session-only) damit man nach Reload nicht in
   * einer leeren App landet. */
  fokusModus: boolean;

  setTheme: (t: Theme) => void;
  setDensity: (d: Density) => void;
  setVorschauModusDefault: (m: VorschauModus) => void;
  setSidebarSichtbar: (b: boolean) => void;
  setTopbarSichtbar: (b: boolean) => void;
  setStatusbarSichtbar: (b: boolean) => void;
  toggleFokus: () => void;
}

const KEYS = {
  theme: "camwosa.theme",
  density: "camwosa.density",
  vorschau: "camwosa.vorschauModus",
  sidebar: "camwosa.sidebarSichtbar",
  topbar: "camwosa.topbarSichtbar",
  statusbar: "camwosa.statusbarSichtbar",
} as const;

function readBool(k: string, fallback: boolean): boolean {
  if (typeof window === "undefined") return fallback;
  const v = window.localStorage.getItem(k);
  if (v === null) return fallback;
  return v === "true";
}

function read<T extends string>(k: string, fallback: T, allowed: readonly T[]): T {
  if (typeof window === "undefined") return fallback;
  const v = window.localStorage.getItem(k);
  return (allowed as readonly string[]).includes(v ?? "") ? (v as T) : fallback;
}

function write(k: string, v: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(k, v);
}

function apply(theme: Theme, density: Density) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.setAttribute("data-density", density);
}

const initialTheme: Theme = read(KEYS.theme, "dark", ["dark", "light"] as const);
const initialDensity: Density = read(KEYS.density, "medium", [
  "compact", "medium", "comfortable",
] as const);
const initialVorschau: VorschauModus = read(KEYS.vorschau, "vereinfacht", [
  "aus", "vereinfacht", "komplett",
] as const);
apply(initialTheme, initialDensity);

export const useUIPrefs = create<UIPrefsState>((set, get) => ({
  theme: initialTheme,
  density: initialDensity,
  vorschauModusDefault: initialVorschau,
  sidebarSichtbar: readBool(KEYS.sidebar, true),
  topbarSichtbar: readBool(KEYS.topbar, true),
  statusbarSichtbar: readBool(KEYS.statusbar, true),
  fokusModus: false,
  setTheme: (t) => {
    write(KEYS.theme, t);
    apply(t, get().density);
    set({ theme: t });
  },
  setDensity: (d) => {
    write(KEYS.density, d);
    apply(get().theme, d);
    set({ density: d });
  },
  setVorschauModusDefault: (m) => {
    write(KEYS.vorschau, m);
    set({ vorschauModusDefault: m });
  },
  setSidebarSichtbar: (b) => {
    write(KEYS.sidebar, String(b));
    set({ sidebarSichtbar: b });
  },
  setTopbarSichtbar: (b) => {
    write(KEYS.topbar, String(b));
    set({ topbarSichtbar: b });
  },
  setStatusbarSichtbar: (b) => {
    write(KEYS.statusbar, String(b));
    set({ statusbarSichtbar: b });
  },
  toggleFokus: () => set({ fokusModus: !get().fokusModus }),
}));
