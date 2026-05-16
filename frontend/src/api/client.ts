import axios from "axios";
import type {
  BohrParameter,
  CheckBericht,
  DXFImportErgebnis,
  FeedsSpeedsErgebnis,
  GeometrieObjekt,
  GravurParameter,
  KonturParameter,
  MaschinenProfil,
  Material,
  PostprozessorInfo,
  TaschenParameter,
  Toolpath,
  Werkzeug,
} from "./types";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

const health = axios.create({ baseURL: "/" });

export const camwosaApi = {
  // Health & Stammdaten
  health: () => health.get("health").then((r) => r.data),
  maschinen: () => api.get<MaschinenProfil[]>("/machines/").then((r) => r.data),
  maschine: (id: string) =>
    api.get<MaschinenProfil>(`/machines/${id}`).then((r) => r.data),
  werkzeuge: () => api.get<Werkzeug[]>("/tools/").then((r) => r.data),
  werkzeug: (id: string) => api.get<Werkzeug>(`/tools/${id}`).then((r) => r.data),
  materialien: () => api.get<Material[]>("/materials/").then((r) => r.data),
  material: (id: string) => api.get<Material>(`/materials/${id}`).then((r) => r.data),
  postprozessoren: () =>
    api.get<PostprozessorInfo[]>("/postprocessors/").then((r) => r.data),

  // Feeds & Speeds
  feedsBerechnen: (
    maschine_id: string,
    werkzeug_id: string,
    material_id: string,
    rpm_wunsch?: number,
  ): Promise<FeedsSpeedsErgebnis> =>
    api
      .post("/feeds/berechnen", { maschine_id, werkzeug_id, material_id, rpm_wunsch })
      .then((r) => r.data),

  // DXF (Legacy-Endpoint, weiter unterstuetzt)
  dxfImport: (datei: File): Promise<DXFImportErgebnis> => {
    const fd = new FormData();
    fd.append("datei", datei);
    return api
      .post("/dxf/import", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },

  // Generischer CAD-Import (DXF, SVG, STL, STEP, ...)
  cadFormate: (): Promise<Array<{
    id: string; name: string; extensions: string[]; beschreibung: string;
  }>> => api.get("/cad/formate").then((r) => r.data),

  cadImport: (datei: File): Promise<DXFImportErgebnis & {
    format_id: string; metadaten?: Record<string, unknown>;
  }> => {
    const fd = new FormData();
    fd.append("datei", datei);
    return api
      .post("/cad/import", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },

  // Operations
  opKontur: (
    werkzeug_id: string,
    geometrie: GeometrieObjekt,
    parameter: KonturParameter,
  ): Promise<Toolpath> =>
    api
      .post("/operations/kontur", { werkzeug_id, geometrie, parameter })
      .then((r) => r.data),

  opTasche: (
    werkzeug_id: string,
    geometrie: GeometrieObjekt,
    parameter: TaschenParameter,
  ): Promise<Toolpath> =>
    api
      .post("/operations/tasche", { werkzeug_id, geometrie, parameter })
      .then((r) => r.data),

  opBohren: (
    werkzeug_id: string,
    punkte: Array<[number, number]>,
    parameter: BohrParameter,
  ): Promise<Toolpath> =>
    api
      .post("/operations/bohren", { werkzeug_id, punkte, parameter })
      .then((r) => r.data),

  opGravur: (
    werkzeug_id: string,
    geometrie: GeometrieObjekt,
    parameter: GravurParameter,
  ): Promise<Toolpath> =>
    api
      .post("/operations/gravur", { werkzeug_id, geometrie, parameter })
      .then((r) => r.data),

  /** Loest Overrides + Material-Preset + Projekt-Defaults zu effektiven Parametern + Quellen auf. */
  opAufloesen: (
    typ: "kontur" | "tasche" | "bohren" | "gravur",
    material_id: string,
    overrides: Record<string, unknown>,
    projekt_defaults?: Record<string, unknown>,
  ): Promise<{ parameter: Record<string, unknown>; quellen: Record<string, string> }> =>
    api.post("/operations/aufloesen", {
      typ, material_id, overrides, projekt_defaults,
    }).then((r) => r.data),

  postprocess: (
    maschine_id: string,
    werkzeug_id: string,
    toolpaths: Toolpath[],
    postprozessor_id?: string,
  ): Promise<{ gcode: string; zeilen: number }> =>
    api
      .post("/operations/postprocess", {
        maschine_id,
        werkzeug_id,
        toolpaths,
        postprozessor_id,
      })
      .then((r) => r.data),

  // Sicherheit
  safetyCheck: (
    maschine_id: string,
    werkzeug_id: string,
    toolpath: Toolpath,
    z_oberkante_material = 0.0,
  ): Promise<CheckBericht> =>
    api
      .post("/safety/check", {
        maschine_id,
        werkzeug_id,
        toolpath,
        z_oberkante_material,
      })
      .then((r) => r.data),

  // Nesting
  nestingRun: (
    teile: unknown[],
    platten: unknown[],
    abstand_zwischen_teilen = 5,
  ) =>
    api
      .post("/nesting/run", { teile, platten, abstand_zwischen_teilen })
      .then((r) => r.data),

  // Workflow
  workflowPruefen: (variante: unknown): Promise<{
    hat_blocker: boolean;
    probleme: Array<{ setup_id: string | null; stufe: string; text: string }>;
  }> => api.post("/workflow/pruefen", { variante }).then((r) => r.data),

  workflowArbeitsplanMd: (
    variante: unknown,
    projekt_name: string,
    maschine_id: string,
  ): Promise<{ markdown: string }> =>
    api.post("/workflow/arbeitsplan", {
      variante, projekt_name, maschine_id, format: "markdown",
    }).then((r) => r.data),

  workflowArbeitsplanPdf: async (
    variante: unknown,
    projekt_name: string,
    maschine_id: string,
  ): Promise<Blob> => {
    const r = await api.post("/workflow/arbeitsplan", {
      variante, projekt_name, maschine_id, format: "pdf",
    }, { responseType: "blob" });
    return r.data as Blob;
  },
};

// Re-export der wichtigsten Typen für bequemen Import
export type { MaschinenProfil, Werkzeug, Material } from "./types";
