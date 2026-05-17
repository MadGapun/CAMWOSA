/**
 * Projekt-IO-Helfer (Master-Plan D4): Bruecke zwischen Frontend-Stores und
 * dem .cwp-Container-Format des Backends.
 *
 * Beim **Speichern**:
 * 1. Snapshot aktive Variante in den Variante-Store schreiben
 *    (passiert intern in `exportiereVarianten`)
 * 2. CWPProjekt-Payload bauen aus allen Stores
 * 3. Backend POST /api/projects/save → Blob
 * 4. Browser-Download via `<a download>`
 *
 * Beim **Laden**:
 * 1. File-Input → File-Object
 * 2. Backend POST /api/projects/load → CWPProjekt-JSON
 * 3. Stores zuruecksetzen + Variante-Store.init() laedt die erste Variante
 *    in die Working-Stores
 */

import { camwosaApi } from "../api/client";
import { useAppStore } from "./store";
import { useProjektStore } from "./projektStore";
import { useRohmaterialStore } from "./rohmaterialStore";
import {
  exportiereVarianten,
  useVarianteStore,
  type VarianteSnapshot,
} from "./varianteStore";
import { useWorkflowStore, type Setup } from "./workflowStore";

interface CWPProjektPayload {
  schema_version: number;
  metadaten: {
    name: string;
    autor: string;
    erstellt: string;
    geaendert: string;
    aktive_variante: string;
  };
  maschine: unknown;
  werkzeuge: unknown[];
  materialien: unknown[];
  geometrien: unknown[];
  varianten: Array<{
    id: string;
    name: string;
    notizen: string;
    rohmaterial: unknown;
    setups: Setup[];
    annotationen: unknown[];
  }>;
  audit_log: string[];
}

/** Baut den vollstaendigen .cwp-Payload aus allen Stores. */
export function projektPayloadAusStores(name: string, autor: string): CWPProjektPayload {
  const store = useAppStore.getState();
  const maschine = store.maschinen.find((m) => m.id === store.aktiveMaschineId);
  if (!maschine) {
    throw new Error("Keine aktive Maschine — bitte erst eine Maschine waehlen.");
  }
  const varianten_data = exportiereVarianten();
  const jetzt = new Date().toISOString();

  return {
    schema_version: 2,
    metadaten: {
      name: name || "Unbenanntes Projekt",
      autor: autor || "",
      erstellt: jetzt,
      geaendert: jetzt,
      aktive_variante: varianten_data.aktive_variante || "default",
    },
    maschine,
    werkzeuge: store.werkzeuge,
    materialien: store.materialien,
    geometrien: store.geometrien,
    varianten: varianten_data.varianten,
    audit_log: [],
  };
}

/** Speichert Projekt als .cwp + triggert Browser-Download. */
export async function projektSpeichern(): Promise<void> {
  const projektState = useProjektStore.getState();
  const name = projektState.dateiname.replace(/\.cwp$/i, "") || "Unbenanntes Projekt";
  const payload = projektPayloadAusStores(name, projektState.autor);
  const blob = await camwosaApi.projektSpeichern(payload);
  _downloadBlob(blob, `${name}.cwp`);
  projektState.setDirty(false);
  projektState.zuletztHinzufuegen(name);
}

/** Speichert unter neuem Namen. */
export async function projektSpeichernAls(neuerName: string): Promise<void> {
  const projektState = useProjektStore.getState();
  projektState.setDateiname(neuerName);
  await projektSpeichern();
}

/** Laedt eine .cwp-Datei und schreibt die Inhalte in die Stores. */
export async function projektLaden(datei: File): Promise<void> {
  const projekt = (await camwosaApi.projektLaden(datei)) as CWPProjektPayload;
  // Aktive Maschine setzen (sonst stimmen Operationen / Spindel-IDs nicht)
  const store = useAppStore.getState();
  if (projekt.maschine && typeof projekt.maschine === "object") {
    const m = projekt.maschine as { id?: string };
    if (m.id) store.setAktiveMaschine(m.id);
  }
  // Geometrien ersetzen
  store.setGeometrien(
    Array.isArray(projekt.geometrien) ? (projekt.geometrien as never[]) : [],
  );
  // Varianten: init() ruft snapshotInStoresLaden() fuer die aktive Variante
  const varianten_snapshots: VarianteSnapshot[] = projekt.varianten.map((v) => ({
    id: v.id,
    name: v.name,
    notizen: v.notizen || "",
    rohmaterial: v.rohmaterial as VarianteSnapshot["rohmaterial"],
    operationen: [],
    setups: (v.setups || []) as Setup[],
  }));
  useVarianteStore.getState().init(
    varianten_snapshots,
    projekt.metadaten?.aktive_variante || null,
  );
  // Projekt-Metadaten
  const projektState = useProjektStore.getState();
  projektState.setDateiname(projekt.metadaten?.name || datei.name);
  projektState.setAutor(projekt.metadaten?.autor || "");
  projektState.setDirty(false);
  projektState.zuletztHinzufuegen(projekt.metadaten?.name || datei.name);
}

/** Setzt alle Stores auf einen leeren Zustand zurueck (= Neues Projekt). */
export function projektNeu(name: string = "Unbenanntes Projekt"): void {
  // Stores leeren
  useAppStore.setState({
    geometrien: [], operationen: [], aktiveOperationId: null,
    aktuellerSicherheitsbericht: null,
    ausgewaehltesSicherheitsergebnisIndex: null,
    ausgewaehlteGeometrieIndex: null,
  });
  useWorkflowStore.setState({ setups: [], erledigt: {} });
  useRohmaterialStore.getState().reset();
  // Variante-Store auf Default zuruecksetzen
  const rohmaterial = useRohmaterialStore.getState().rohmaterial;
  useVarianteStore.getState().init([{
    id: "default", name: "Default", notizen: "",
    rohmaterial, operationen: [], setups: [],
  }], "default");
  // Projekt-Metadaten
  const projektState = useProjektStore.getState();
  projektState.setDateiname(name);
  projektState.setDirty(false);
}

/** Startet einen Browser-Download fuer einen Blob. */
function _downloadBlob(blob: Blob, dateiname: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = dateiname;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(url);
    a.remove();
  }, 100);
}
