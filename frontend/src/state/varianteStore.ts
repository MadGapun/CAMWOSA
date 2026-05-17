import { create } from "zustand";
import type { GeometrieObjekt, OperationEintrag } from "../api/types";
import type { Rohmaterial } from "./rohmaterialStore";
import { useRohmaterialStore } from "./rohmaterialStore";
import { useAppStore } from "./store";
import { useWorkflowStore, type Setup } from "./workflowStore";

/**
 * Varianten-Store (Master-Plan A19).
 *
 * Eine Variante ist eine vollstaendige Auspraegung eines Projekts: eigene
 * Operations-Liste, eigene Setups, eigenes Rohmaterial, eigene Annotationen.
 * Geometrien werden **geteilt** (eine Variante einer Tuer ist immer noch die
 * gleiche Tuer geometrisch — nur die Bearbeitungsstrategie unterscheidet sich).
 *
 * Backend-Pendant: `Variante` in `backend/camwosa/project/schema.py`.
 *
 * **Snapshot-Logik:** beim Wechsel der aktiven Variante wird der aktuelle
 * Inhalt der Working-Stores (operationen, setups, rohmaterial) in die alte
 * Variante zurueckgeschrieben, dann der Inhalt der neuen Variante in die
 * Stores geladen. So bleibt die User-UX dieselbe wie ohne Varianten —
 * Varianten sind reine Snapshot-Aufbewahrung.
 *
 * Geometrien werden bewusst nicht im Variante-Snapshot gespeichert, sondern
 * verbleiben global im `useAppStore.geometrien` (geteilt zwischen Varianten).
 * Wer pro Variante andere Geometrien will, sollte ein neues Projekt anlegen.
 */

export interface VarianteSnapshot {
  id: string;
  name: string;
  notizen: string;
  /** Snapshots der Working-Stores. Wird beim Wechsel geladen/geschrieben. */
  rohmaterial: Rohmaterial;
  operationen: OperationEintrag[];
  setups: Setup[];
}

interface VarianteState {
  varianten: VarianteSnapshot[];
  aktiveVarianteId: string | null;

  /** Initial-Setup beim Laden eines Projekts oder beim Erstellen.
   *  Setzt die Liste komplett neu, ohne Snapshot zu schreiben. */
  init: (varianten: VarianteSnapshot[], aktiveId: string | null) => void;

  /** Wechselt die aktive Variante.
   *  1. Schreibt den aktuellen Store-Stand in die bisherige aktive Variante.
   *  2. Laedt die neue Variante in die Working-Stores.
   *  No-op wenn ``neueId`` bereits aktiv ist. */
  wechseln: (neueId: string) => void;

  /** Erstellt eine neue Variante, optional als Duplikat einer bestehenden.
   *  Wechselt direkt zur neuen Variante. Gibt die neue id zurueck. */
  erstellen: (name: string, dupliziereVon?: string) => string;

  /** Benennt eine Variante um (Live, auch wenn nicht aktiv). */
  umbenennen: (id: string, name: string) => void;

  /** Aendert die Notizen einer Variante. */
  notizenSetzen: (id: string, notizen: string) => void;

  /** Loescht eine Variante. Wenn die aktive Variante geloescht wird, wird
   *  auf die erste verbleibende gewechselt. Die letzte Variante kann nicht
   *  geloescht werden (silent no-op). */
  loeschen: (id: string) => void;
}

/** Liest den aktuellen Stand der Working-Stores in ein Snapshot-Objekt. */
function snapshotAusStores(id: string, name: string, notizen: string): VarianteSnapshot {
  return {
    id,
    name,
    notizen,
    rohmaterial: { ...useRohmaterialStore.getState().rohmaterial },
    operationen: [...useAppStore.getState().operationen],
    setups: [...useWorkflowStore.getState().setups],
  };
}

/** Schreibt einen Snapshot in die Working-Stores. */
function snapshotInStoresLaden(snap: VarianteSnapshot): void {
  // Rohmaterial: ganzes Objekt durchsetzen
  useRohmaterialStore.setState({ rohmaterial: { ...snap.rohmaterial } });
  // Operationen: ersetzen, aktive Operation deselektieren falls sie nicht mehr existiert
  useAppStore.setState((s) => {
    const operationen = [...snap.operationen];
    const aktiveOperationId = operationen.some((o) => o.id === s.aktiveOperationId)
      ? s.aktiveOperationId
      : null;
    return { operationen, aktiveOperationId };
  });
  // Setups: ersetzen + Checkliste zuruecksetzen
  useWorkflowStore.setState({ setups: [...snap.setups], erledigt: {} });
}

function neueId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
}

const DEFAULT_VARIANTE: VarianteSnapshot = {
  id: "default",
  name: "Default",
  notizen: "",
  rohmaterial: useRohmaterialStore.getState().rohmaterial,
  operationen: [],
  setups: [],
};

export const useVarianteStore = create<VarianteState>((set, get) => ({
  varianten: [DEFAULT_VARIANTE],
  aktiveVarianteId: "default",

  init: (varianten, aktiveId) => {
    const liste = varianten.length > 0 ? varianten : [DEFAULT_VARIANTE];
    const aktiv = aktiveId && liste.some((v) => v.id === aktiveId) ? aktiveId : liste[0].id;
    set({ varianten: liste, aktiveVarianteId: aktiv });
    const aktive = liste.find((v) => v.id === aktiv);
    if (aktive) snapshotInStoresLaden(aktive);
  },

  wechseln: (neueId) => {
    const { aktiveVarianteId, varianten } = get();
    if (neueId === aktiveVarianteId) return;
    const neueVariante = varianten.find((v) => v.id === neueId);
    if (!neueVariante) return;
    // 1. Snapshot der aktuellen Working-Stores in die bisherige Variante
    const aktualisiert = varianten.map((v) => {
      if (v.id === aktiveVarianteId) {
        return snapshotAusStores(v.id, v.name, v.notizen);
      }
      return v;
    });
    set({ varianten: aktualisiert, aktiveVarianteId: neueId });
    // 2. Neue Variante in die Working-Stores laden
    snapshotInStoresLaden(neueVariante);
  },

  erstellen: (name, dupliziereVon) => {
    const { varianten, aktiveVarianteId } = get();
    const id = neueId("variante");
    // Erst den aktuellen Stand sichern
    const gesichert = varianten.map((v) =>
      v.id === aktiveVarianteId ? snapshotAusStores(v.id, v.name, v.notizen) : v,
    );
    // Quelle: explizit gewaehlt, sonst aktive
    const quelle = gesichert.find((v) => v.id === (dupliziereVon ?? aktiveVarianteId));
    const neueVariante: VarianteSnapshot = quelle
      ? {
          id,
          name,
          notizen: "",
          rohmaterial: { ...quelle.rohmaterial },
          // tiefe Klone der Operationen + Setups
          operationen: quelle.operationen.map((o) => ({ ...o, id: neueId("op") })),
          setups: quelle.setups.map((s) => ({ ...s, id: neueId("setup") })),
        }
      : {
          id,
          name,
          notizen: "",
          rohmaterial: { ...useRohmaterialStore.getState().rohmaterial },
          operationen: [],
          setups: [],
        };
    set({ varianten: [...gesichert, neueVariante], aktiveVarianteId: id });
    snapshotInStoresLaden(neueVariante);
    return id;
  },

  umbenennen: (id, name) => {
    set((s) => ({
      varianten: s.varianten.map((v) => (v.id === id ? { ...v, name } : v)),
    }));
  },

  notizenSetzen: (id, notizen) => {
    set((s) => ({
      varianten: s.varianten.map((v) => (v.id === id ? { ...v, notizen } : v)),
    }));
  },

  loeschen: (id) => {
    const { varianten, aktiveVarianteId } = get();
    if (varianten.length <= 1) return; // letzte Variante bleibt
    const verbleibend = varianten.filter((v) => v.id !== id);
    let neueAktiveId = aktiveVarianteId;
    if (id === aktiveVarianteId) {
      neueAktiveId = verbleibend[0].id;
      snapshotInStoresLaden(verbleibend[0]);
    }
    set({ varianten: verbleibend, aktiveVarianteId: neueAktiveId });
  },
}));

/** Selector: aktive Variante. */
export const useAktiveVariante = () =>
  useVarianteStore((s) => s.varianten.find((v) => v.id === s.aktiveVarianteId) ?? null);

/** Hilfs-Selector zum Mappen in CWP-Projekt-Format (fuer Save). */
export function exportiereVarianten(): {
  varianten: Array<{
    id: string;
    name: string;
    notizen: string;
    rohmaterial: Rohmaterial;
    setups: Setup[];
    annotationen: never[];
  }>;
  aktive_variante: string | null;
} {
  const { varianten, aktiveVarianteId } = useVarianteStore.getState();
  // Vor dem Export Snapshot der aktiven Variante aktualisieren
  const aktualisiert = varianten.map((v) =>
    v.id === aktiveVarianteId ? snapshotAusStores(v.id, v.name, v.notizen) : v,
  );
  return {
    aktive_variante: aktiveVarianteId,
    varianten: aktualisiert.map((v) => ({
      id: v.id,
      name: v.name,
      notizen: v.notizen,
      rohmaterial: v.rohmaterial,
      setups: v.setups,
      annotationen: [],
    })),
  };
}

// Re-Export zur Bequemlichkeit
export type { GeometrieObjekt };
