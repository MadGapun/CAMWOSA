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
import type { GeometrieObjekt, OperationEintrag } from "../api/types";
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

/**
 * Uebernimmt ein bereits serverseitig erzeugtes QuickCAM-Projekt (Issue #50)
 * in die flachen Working-Stores. Der Payload kommt direkt aus
 * /api/quickcam/erzeugen (NICHT aus /projects/load).
 *
 * QuickCAM-Besonderheiten (backend/.../quickcam/templates.py):
 *  - Operationen liegen in varianten[0].setups[].operationen (nicht flach)
 *  - Geometrie steckt in op.parameter['__geometrie'], geometrien=[] global
 * Beides wird hier in die flachen Stores (operationen/geometrien) ausgepackt,
 * die OperationenView/ZeichnenView lesen.
 */
export function quickcamProjektInStores(projektRaw: unknown): void {
  const projekt = projektRaw as CWPProjektPayload;
  const store = useAppStore.getState();

  // 1. Aktive Maschine setzen (sonst stimmen Spindel-/Werkzeug-IDs nicht)
  const m = projekt.maschine as { id?: string } | undefined;
  if (m?.id) store.setAktiveMaschine(m.id);

  // 2. Operationen aus setups ausflachen + Geometrien aus op.parameter heben
  const flacheOps: OperationEintrag[] = [];
  const geometrien: GeometrieObjekt[] = [];
  const v0 = (projekt.varianten ?? [])[0];
  for (const setup of (v0?.setups ?? []) as Array<{ operationen?: unknown[] }>) {
    for (const opRaw of setup.operationen ?? []) {
      const op = opRaw as OperationEintrag & {
        parameter?: Record<string, unknown> & { __geometrie?: GeometrieObjekt };
      };
      const geo = op.parameter?.__geometrie;
      let geometrie_ids = op.geometrie_ids ?? [];
      if (geo) {
        const gid = geo.id ?? `geo_${op.id}`;
        geometrien.push({ ...geo, id: gid });
        geometrie_ids = [gid];
      }
      flacheOps.push({ ...op, geometrie_ids, aktiviert: op.aktiviert ?? true } as OperationEintrag);
    }
  }

  // 3. Flache Stores setzen (genau das, was OperationenView/ZeichnenView lesen)
  store.setGeometrien(geometrien as never[]);
  useAppStore.setState({
    operationen: flacheOps,
    aktiveOperationId: flacheOps[0]?.id ?? null,
  });

  // 4. Rohmaterial + Setups in ihre Stores
  if (v0?.rohmaterial && typeof v0.rohmaterial === "object") {
    useRohmaterialStore.getState().setze(v0.rohmaterial as never);
  }
  useWorkflowStore.setState({ setups: (v0?.setups ?? []) as Setup[], erledigt: {} });

  // 5. Projekt-Metadaten (dirty = ungespeichert)
  const projektState = useProjektStore.getState();
  projektState.setDateiname(projekt.metadaten?.name || "QuickCAM-Projekt");
  projektState.setDirty(true);
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
