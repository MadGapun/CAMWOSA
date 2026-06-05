import axios from "axios";
import type {
  BohrParameter,
  CheckBericht,
  DrechselParameter,
  DXFImportErgebnis,
  FeedsSpeedsErgebnis,
  GeometrieObjekt,
  GravurParameter,
  KonturParameter,
  MachineBundle,
  MaschinenProfil,
  Material,
  PostprozessorInfo,
  RotaryProfil,
  Spindel,
  TaschenParameter,
  Toolpath,
  Werkzeug,
} from "./types";

/**
 * baseURL-Strategie:
 * - Dev (http://localhost:5173): Vite proxyt /api + /health auf 127.0.0.1:8765
 *   → relative URLs reichen.
 * - Production (file://, Electron): kein Proxy. Wir holen die echte Backend-URL
 *   vom Main-Process via window.camwosa.backendUrl() und stellen sie axios als
 *   `baseURL` voran. Der Port ist dynamisch (findFreePort 8765+).
 */
export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

const health = axios.create({ baseURL: "/" });

// In Electron-Production die echte Backend-URL aus dem Main-Process holen.
// Wir mutieren die axios-defaults — alle nachfolgenden Aufrufe gehen dann
// gegen http://127.0.0.1:<freier-port> statt gegen file:///.
async function initBackendBaseUrl(): Promise<void> {
  const camwosa = (window as unknown as {
    camwosa?: { backendUrl?: () => Promise<string> };
  }).camwosa;
  if (!camwosa?.backendUrl) return;  // Nicht in Electron → Dev-Server-Proxy
  try {
    const baseUrl = await camwosa.backendUrl();
    api.defaults.baseURL = `${baseUrl}/api`;
    health.defaults.baseURL = baseUrl;
  } catch (e) {
    console.warn("[api] backendUrl-Lookup fehlgeschlagen, bleibe bei /api", e);
  }
}

// Eager-init: lauft asynchron beim Modul-Load. Nachfolgende API-Calls warten
// nicht explizit auf den Init — aber da React initial einen Loading-State hat
// (siehe useEffect-Polling in App.tsx) ist das in der Praxis kein Problem.
// Wer absolut sicher gehen will, kann auf `apiBereit` warten.
export const apiBereit: Promise<void> = initBackendBaseUrl();

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
  spindeln: () => api.get<Spindel[]>("/spindles/").then((r) => r.data),
  spindel: (id: string) => api.get<Spindel>(`/spindles/${id}`).then((r) => r.data),
  postprozessoren: () =>
    api.get<PostprozessorInfo[]>("/postprocessors/").then((r) => r.data),

  // Maschinen-Sharing (Bundle inkl. Spindeln)
  machineExport: (id: string): Promise<MachineBundle> =>
    api.get(`/machines/${id}/export`).then((r) => r.data),
  machineImport: (bundle: MachineBundle): Promise<{
    gueltig: boolean; maschine: MaschinenProfil; spindeln: Spindel[]; fehler?: string;
  }> => api.post("/machines/import", bundle).then((r) => r.data),

  // Maschine CRUD (Issue #22 — First-Run-Wizard inline-Anlegen)
  maschineAnlegen: (m: MaschinenProfil): Promise<{ gespeichert: boolean; maschine: MaschinenProfil }> =>
    api.post("/machines/", m).then((r) => r.data),
  maschineUpdaten: (id: string, m: MaschinenProfil): Promise<{ gespeichert: boolean; maschine: MaschinenProfil }> =>
    api.put(`/machines/${id}`, m).then((r) => r.data),
  maschineLoeschen: (id: string): Promise<{ geloescht: boolean }> =>
    api.delete(`/machines/${id}`).then((r) => r.data),

  // Spindel CRUD
  spindelAnlegen: (s: Spindel): Promise<{ gespeichert: boolean; spindel: Spindel }> =>
    api.post("/spindles/", s).then((r) => r.data),
  spindelUpdaten: (id: string, s: Spindel): Promise<{ gespeichert: boolean; spindel: Spindel }> =>
    api.put(`/spindles/${id}`, s).then((r) => r.data),
  spindelLoeschen: (id: string): Promise<{ geloescht: boolean }> =>
    api.delete(`/spindles/${id}`).then((r) => r.data),

  // Rotary-Profil CRUD (alles editierbar)
  rotaryProfile: (): Promise<RotaryProfil[]> =>
    api.get<RotaryProfil[]>("/rotary/profile").then((r) => r.data),
  rotaryProfilAnlegen: (p: RotaryProfil): Promise<{ gespeichert: boolean; rotary_profil: RotaryProfil }> =>
    api.post("/rotary/profile", p).then((r) => r.data),
  rotaryProfilUpdaten: (id: string, p: RotaryProfil): Promise<{ gespeichert: boolean; rotary_profil: RotaryProfil }> =>
    api.put(`/rotary/profile/${id}`, p).then((r) => r.data),
  rotaryProfilLoeschen: (id: string): Promise<{ geloescht: boolean }> =>
    api.delete(`/rotary/profile/${id}`).then((r) => r.data),

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

  // Bitmap → Vektor-Trace (alpha.9, Cluster L1)
  bitmapTrace: (
    datei: File,
    optionen?: {
      schwelle?: number; invertieren?: boolean; pixel_pro_mm?: number;
      ziel_breite_mm?: number; glaettung_toleranz_mm?: number; min_flaeche_mm2?: number;
    },
  ): Promise<{
    anzahl: number;
    objekte: Array<{ typ: string; layer: string; geschlossen: boolean; punkte: Array<[number, number]> }>;
  }> => {
    const fd = new FormData();
    fd.append("datei", datei);
    for (const [k, v] of Object.entries(optionen ?? {})) {
      if (v !== null && v !== undefined) fd.append(k, String(v));
    }
    return api
      .post("/cad/bitmap-trace", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },

  // Zeit-/Aufwand-Schätzung (alpha.9, Cluster K5)
  zeitschaetzung: (
    toolpaths: Array<Record<string, unknown>>,
    optionen: { maschine_id?: string; eilgang_mm_min?: number; overhead_faktor?: number; werkzeugwechsel_sekunden?: number },
  ): Promise<{
    schnitt_sekunden: number; eilgang_sekunden: number; pausen_sekunden: number;
    gesamt_sekunden: number; gesamt_minuten: number; klartext: string;
  }> =>
    api.post("/operations/zeitschaetzung", { toolpaths, ...optionen }).then((r) => r.data),

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

  // Bild → Heightmap (Phase A der Bild-zu-Relief-Pipeline)
  bildZuHeightmap: async (
    datei: File,
    parameter: {
      max_tiefe_mm?: number;
      pixel_pro_mm?: number;
      invertieren?: boolean;
      glaetten_radius?: number;
      zero_plane_schwelle?: number;
      max_dimension_px?: number | null;
    } = {},
  ): Promise<{
    aufloesung_mm: number;
    x_min_mm: number;
    y_min_mm: number;
    z_max_mm: number;
    shape: [number, number];
    z_values_base64: string;
    z_values_dtype: string;
    statistik: {
      shape_x: number; shape_y: number; anzahl_pixel: number;
      aufloesung_mm: number; breite_mm: number; hoehe_mm: number;
      z_min: number; z_max: number; z_mittel: number; max_tiefe_mm: number;
    };
  }> => {
    const fd = new FormData();
    fd.append("datei", datei);
    for (const [k, v] of Object.entries(parameter)) {
      if (v !== null && v !== undefined) fd.append(k, String(v));
    }
    const r = await api.post("/heightmap/aus-bild", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return r.data;
  },

  // --- Heightmap-Bearbeitungs-Filter (Master-Plan A35 / Phase D) ---

  heightmapFilter: async (
    name:
      | "gamma" | "histogramm-stretch" | "zero-plane"
      | "edge-boost" | "selective-smoothing" | "detail-slider",
    heightmap: unknown,
    parameter: Record<string, unknown>,
  ): Promise<unknown> => {
    const r = await api.post(`/heightmap/bearbeitung/${name}`, {
      heightmap, ...parameter,
    });
    return r.data;
  },

  // --- AI-Tiefenkarte (Master-Plan A36 / Phase E, optional [ai]-Extra) ---

  aiModelle: (): Promise<{
    ist_installiert: boolean;
    default: string;
    modelle: Record<string, { huggingface: string; groesse_mb: string; qualitaet: string }>;
  }> => api.get("/heightmap/ai/modelle").then((r) => r.data),

  bildZuHeightmapAi: async (
    datei: File,
    parameter: {
      max_tiefe_mm?: number;
      pixel_pro_mm?: number;
      modell?: string;
      invertieren?: boolean;
      max_dimension_px?: number;
    } = {},
  ): Promise<unknown> => {
    const fd = new FormData();
    fd.append("datei", datei);
    for (const [k, v] of Object.entries(parameter)) {
      if (v !== null && v !== undefined) fd.append(k, String(v));
    }
    const r = await api.post("/heightmap/aus-bild-ai", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return r.data;
  },

  // Voxel-Material-Abtrag-Simulation
  voxelSimulation: (
    toolpaths: unknown[],
    werkzeug_id: string,
    werkstueck: {
      laenge_x: number; breite_y: number; hoehe_z: number;
      nullpunkt_x?: number; nullpunkt_y?: number;
    },
    aufloesung_mm = 2.0,
    z_oberkante_material?: number,
  ): Promise<{
    aufloesung_mm: number;
    nx: number; ny: number; nz: number;
    werkstueck: typeof werkstueck;
    boundary_voxel: Array<[number, number, number]>;
    voxel_count: number;
    voxel_volumen_mm3: number;
    abgetragenes_volumen_mm3: number;
    bewegungen_simuliert: number;
  }> => api.post("/simulation/voxel", {
    toolpaths, werkzeug_id, werkstueck, aufloesung_mm, z_oberkante_material,
  }).then((r) => r.data),

  opDrechseln: (
    werkzeug_id: string,
    parameter: DrechselParameter,
  ): Promise<Toolpath> =>
    api
      .post("/operations/drechseln", { werkzeug_id, parameter })
      .then((r) => r.data),

  opWrap: (
    werkzeug_id: string,
    punkte_xy: Array<[number, number]>,
    parameter: Record<string, unknown>,
  ): Promise<Toolpath & { warnungen?: string[] }> =>
    api
      .post("/operations/wrap", { werkzeug_id, punkte_xy, parameter })
      .then((r) => r.data),

  opWrapPruefe: (
    punkte_xy: Array<[number, number]>,
    werkstueck_radius_mm: number,
  ): Promise<{ gueltig: boolean; warnungen: string[] }> =>
    api
      .post("/operations/wrap/pruefe", { punkte_xy, werkstueck_radius_mm })
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
    optionen?: {
      fahrweg_optimierung?: boolean;
      freifahrt_hoehe?: number | null;
      arc_fitting?: boolean;
      arc_toleranz_mm?: number;
      modal?: boolean;
      rapid_safety?: boolean;
      spindel_hochlauf_s?: number | null;
      rampe_eintauchen?: boolean;
      rampen_winkel_grad?: number;
      rampen_vorschub?: number | null;
      rampen_vorschub_faktor?: number;
    },
  ): Promise<{ gcode: string; zeilen: number }> =>
    api
      .post("/operations/postprocess", {
        maschine_id,
        werkzeug_id,
        toolpaths,
        postprozessor_id,
        ...optionen,
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

  // Werkzeug-Standzeit
  standzeitListe: (): Promise<Array<{
    werkzeug_id: string; name: string;
    genutzt_minuten: number; max_minuten: number | null;
    prozent: number | null; warnung: boolean; kritisch: boolean;
  }>> => api.get("/standzeit/").then((r) => r.data),
  standzeitReset: (werkzeug_id: string): Promise<{ ok: boolean }> =>
    api.post(`/standzeit/reset/${werkzeug_id}`).then((r) => r.data),
  standzeitAddieren: (werkzeug_id: string, minuten: number): Promise<{ ok: boolean }> =>
    api.post("/standzeit/addiere", { werkzeug_id, minuten }).then((r) => r.data),

  // Werkzeug CRUD
  werkzeugAnlegen: (w: Werkzeug): Promise<{ gespeichert: boolean; werkzeug: Werkzeug }> =>
    api.post("/tools/", w).then((r) => r.data),
  werkzeugUpdaten: (id: string, w: Werkzeug): Promise<{ gespeichert: boolean; werkzeug: Werkzeug }> =>
    api.put(`/tools/${id}`, w).then((r) => r.data),
  werkzeugLoeschen: (id: string): Promise<{ geloescht: boolean }> =>
    api.delete(`/tools/${id}`).then((r) => r.data),
  vBitSpitze: (
    spitzenwinkel_grad: number, schneidlaenge_mm: number, durchmesser_max_mm: number,
  ): Promise<{ spitzendurchmesser_mm: number }> =>
    api.post("/tools/helper/v-bit-spitzendurchmesser", {
      spitzenwinkel_grad, schneidlaenge_mm, durchmesser_max_mm,
    }).then((r) => r.data),
  vBitWinkel: (
    spitzendurchmesser_mm: number, durchmesser_max_mm: number, schneidlaenge_mm: number,
  ): Promise<{ spitzenwinkel_grad: number }> =>
    api.post("/tools/helper/v-bit-winkel", {
      spitzendurchmesser_mm, durchmesser_max_mm, schneidlaenge_mm,
    }).then((r) => r.data),

  // Material CRUD
  materialAnlegen: (m: Material): Promise<{ gespeichert: boolean; material: Material }> =>
    api.post("/materials/", m).then((r) => r.data),
  materialUpdaten: (id: string, m: Material): Promise<{ gespeichert: boolean; material: Material }> =>
    api.put(`/materials/${id}`, m).then((r) => r.data),
  materialLoeschen: (id: string): Promise<{ geloescht: boolean }> =>
    api.delete(`/materials/${id}`).then((r) => r.data),

  // Diagnose: Z-Grid-Analyse (alpha.5, A47-Rest)
  zGridAnalysieren: (daten: {
    messpunkte: Array<{ x: number; y: number; z: number }>;
    werkzeug_typ?: string;
    bezugs_z?: number | null;
  }): Promise<{
    befund: "eben_ok" | "leichte_neigung" | "starke_neigung" | "unebene_oberflaeche";
    klartext: string;
    empfehlung: string;
    anzahl_punkte: number;
    z_min: number; z_max: number; z_spreizung: number; z_std: number;
    neigung_grad: number; neigung_richtung_grad: number;
    max_lokale_abweichung_mm: number;
    abweichungen: number[];
  }> => api.post("/diagnostics/z-grid", daten).then((r) => r.data),

  // Spezial-Operationen (alpha.5, Cluster E + B)
  dragEngraving: (
    parameter: Record<string, unknown>,
    geometrie: Record<string, unknown> | Array<Record<string, unknown>>,
  ): Promise<Record<string, unknown>> =>
    api.post("/spezial-ops/drag-engraving", { parameter, geometrie }).then((r) => r.data),
  autoInlay: (
    parameter: { spiel_mm?: number; werkzeug_radius_mm: number; tasche_tiefe_mm?: number; plug_uebermass_oben_mm?: number },
    geometrie: Record<string, unknown>,
  ): Promise<{
    ergebnis: Record<string, unknown>;
    tasche_geometrie: Record<string, unknown>;
    plug_geometrie: Record<string, unknown>;
  }> => api.post("/spezial-ops/auto-inlay", { parameter, geometrie }).then((r) => r.data),
  threadMilling: (
    parameter: Record<string, unknown>,
  ): Promise<Record<string, unknown>> =>
    api.post("/spezial-ops/thread-milling", { parameter }).then((r) => r.data),
  circularPocketPfade: (
    parameter: Record<string, unknown>,
  ): Promise<{ pfade: Array<Array<[number, number]>>; anzahl: number }> =>
    api.post("/spezial-ops/circular-pocket-pfade", parameter).then((r) => r.data),
  radialPocketPfade: (
    parameter: Record<string, unknown>,
  ): Promise<{ pfade: Array<Array<[number, number]>>; anzahl: number }> =>
    api.post("/spezial-ops/radial-pocket-pfade", parameter).then((r) => r.data),

  // 3D-Frässtrategien (alpha.6, Cluster I)
  planfraesen: (
    parameter: Record<string, unknown>,
  ): Promise<Record<string, unknown>> =>
    api.post("/spezial-ops/planfraesen", { parameter }).then((r) => r.data),
  dreiDParallel: (
    parameter: Record<string, unknown>,
    heightmap: {
      shape: [number, number]; aufloesung: number;
      x_min: number; y_min: number; z_max: number;
      z_values_dtype: string; z_values_base64: string;
    },
  ): Promise<Record<string, unknown>> =>
    api.post("/spezial-ops/3d-parallel", { parameter, heightmap }).then((r) => r.data),

  // Geometrie-Annotationen
  annotationTypen: (): Promise<string[]> =>
    api.get("/annotationen/typen").then((r) => r.data),
  annotationValidieren: (a: Record<string, unknown>): Promise<{
    gueltig: boolean; annotation?: Record<string, unknown>; fehler?: string;
  }> => api.post("/annotationen/validate", a).then((r) => r.data),
  annotationListeValidieren: (annotationen: Array<Record<string, unknown>>): Promise<{
    gueltig: boolean;
    annotationen: Array<Record<string, unknown>>;
    fehler: Array<{ index: number; fehler: string }>;
  }> => api.post("/annotationen/validate-liste", { annotationen }).then((r) => r.data),
  annotationenZuOperationen: (
    annotationen: Array<Record<string, unknown>>,
    werkzeug_ids?: string[],
  ): Promise<{
    operationen: Array<{ id: string; name: string; typ: string; parameter: Record<string, unknown> }>;
    hinweise: string[];
  }> => api.post("/annotationen/zu-operationen", {
    annotationen, werkzeug_ids,
  }).then((r) => r.data),

  // Quick-CAM
  quickcamTemplates: (): Promise<Array<{
    id: string; name: string; kurzbeschreibung: string; icon: string;
    operation_typ: string;
    parameter: Array<{
      name: string; label: string; typ: string;
      default: unknown; einheit?: string; hinweis?: string;
    }>;
  }>> => api.get("/quickcam/templates").then((r) => r.data),

  quickcamErzeugen: (
    template_id: string,
    eingaben: Record<string, unknown>,
    maschine_id: string,
    werkzeug_id: string,
    material_id: string,
    projekt_name?: string,
  ): Promise<{ projekt: unknown }> =>
    api.post("/quickcam/erzeugen", {
      template_id, eingaben, maschine_id, werkzeug_id, material_id, projekt_name,
    }).then((r) => r.data),

  // CuttingPresets
  cuttingPresets: (filter?: {
    material_id?: string; werkzeug_id?: string; operation_typ?: string;
  }): Promise<Array<{
    id: string; name: string; material_id: string; werkzeug_id: string;
    operation_typ: string;
    rpm: number; vorschub: number; plunge: number;
    stepdown: number; stepover_prozent: number;
    notizen?: string;
  }>> => api.get("/cutting-presets/", { params: filter }).then((r) => r.data),
  cuttingPresetSpeichern: (preset: Record<string, unknown>) =>
    api.post("/cutting-presets/", preset).then((r) => r.data),
  cuttingPresetLoeschen: (id: string) =>
    api.delete(`/cutting-presets/${id}`).then((r) => r.data),

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

  // --- Projekt-Persistenz (Master-Plan D4) ---

  projektNeu: (
    name: string,
    maschine_id: string,
    rohmaterial: unknown,
    autor: string = "",
  ): Promise<unknown> =>
    api.post("/projects/new", { name, maschine_id, rohmaterial, autor })
       .then((r) => r.data),

  projektSpeichern: async (projekt: unknown): Promise<Blob> => {
    const r = await api.post("/projects/save", projekt, { responseType: "blob" });
    return r.data as Blob;
  },

  projektLaden: async (datei: File): Promise<unknown> => {
    const fd = new FormData();
    fd.append("datei", datei);
    const r = await api.post("/projects/load", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return r.data;
  },
};

// Re-export der wichtigsten Typen für bequemen Import
export type { MaschinenProfil, Werkzeug, Material } from "./types";
