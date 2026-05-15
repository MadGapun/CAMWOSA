import axios from "axios";

const baseURL = "/api";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export interface MaschinenProfil {
  id: string;
  name: string;
  hersteller: string;
  modell: string;
  controller: string;
  arbeitsraum: { x: number; y: number; z: number };
  max_vorschub: number;
  sicherer_vorschub: number;
  eilgang: number;
  spindel_typ: string;
  spindel_rpm_min: number;
  spindel_rpm_max: number;
  postprozessor: string;
  modi: string[];
  aktiver_modus: string;
}

export interface Werkzeug {
  id: string;
  name: string;
  typ: string;
  durchmesser: number;
  schneiden: number;
  schneidlaenge: number;
  gesamtlaenge: number;
}

export interface Material {
  id: string;
  name: string;
  kategorie: string;
  unter_kategorie?: string;
  janka_haerte?: number;
  presets: Array<{
    werkzeug_id: string;
    rpm: number;
    vorschub: number;
    plunge: number;
    stepdown: number;
    stepover_prozent: number;
  }>;
}

export const camwosaApi = {
  health: () => api.get("/../health").then((r) => r.data),
  maschinen: () => api.get<MaschinenProfil[]>("/machines/").then((r) => r.data),
  werkzeuge: () => api.get<Werkzeug[]>("/tools/").then((r) => r.data),
  materialien: () => api.get<Material[]>("/materials/").then((r) => r.data),
  postprozessoren: () => api.get("/postprocessors/").then((r) => r.data),
  feedsBerechnen: (maschine_id: string, werkzeug_id: string, material_id: string, rpm_wunsch?: number) =>
    api.post("/feeds/berechnen", { maschine_id, werkzeug_id, material_id, rpm_wunsch }).then((r) => r.data),
  nestingRun: (teile: unknown[], platten: unknown[], abstand_zwischen_teilen = 5) =>
    api.post("/nesting/run", { teile, platten, abstand_zwischen_teilen }).then((r) => r.data),
};
