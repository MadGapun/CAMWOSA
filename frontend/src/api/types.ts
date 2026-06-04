/**
 * TypeScript-Typen, die das Backend-Datenmodell spiegeln.
 * Synchron zu backend/camwosa/db/models.py + gcode/toolpath.py + cam/parameter.py.
 */

// --- Stammdaten ---

export type ControllerTyp = "GRBL" | "Marlin" | "LinuxCNC" | "Mach3" | "Duet" | "Sonstige";
export type SpindelTyp = "manuell" | "PWM" | "analog";
export type MaschinenModus = "standard_xyz" | "rotary_y" | "rotary_x" | "laser" | "drag_knife";

export interface Arbeitsraum { x: number; y: number; z: number }

export type SpindelHerkunft = "oem" | "upgrade" | "eigenbau";

export interface Spindel {
  id: string;
  name: string;
  hersteller: string;
  modell: string;
  typ: SpindelTyp;
  rpm_min: number;
  rpm_max: number;
  leistung_watt?: number | null;
  drehmoment_ncm?: number | null;
  gewicht_g?: number | null;
  schaft_durchmesser_mm?: number | null;
  kuehlung: string;
  pwm_min_promille?: number | null;
  pwm_max_promille?: number | null;
  rampen_zeit_s?: number | null;
  herkunft: SpindelHerkunft;
  notizen?: string;
}

export interface MaschinenProfil {
  id: string;
  name: string;
  hersteller: string;
  modell: string;
  controller: ControllerTyp;
  arbeitsraum: Arbeitsraum;
  max_vorschub: number;
  sicherer_vorschub: number;
  eilgang: number;
  spindel_ids: string[];
  aktive_spindel_id?: string | null;
  spindel_typ: SpindelTyp;
  spindel_rpm_min: number;
  spindel_rpm_max: number;
  sicherheitshoehe: number;
  werkzeugwechsel_position?: [number, number, number] | null;
  postprozessor: string;
  modi: MaschinenModus[];
  aktiver_modus: MaschinenModus;
  notizen?: string;
  /** Server-Anreicherung */
  _aktive_spindel?: Spindel | null;
  _verfuegbare_spindeln?: Spindel[];
  _effektive_rpm_min?: number;
  _effektive_rpm_max?: number;
}

export interface MachineBundle {
  schema_version: number;
  typ: "camwosa.machine_bundle";
  maschine: MaschinenProfil;
  spindeln: Spindel[];
}

export type WerkzeugTyp =
  | "schaftfraeser" | "kugelfraeser" | "torusfraeser"
  | "v_bit" | "ballnose_v_bit" | "gravierstichel" | "bohrer"
  | "einschneider" | "fischschwanz" | "schruppfraeser"
  | "diamantgravierer" | "drag_gravierer";

export interface WerkzeugSegment {
  z_unten: number;
  z_oben: number;
  durchmesser_unten: number;
  durchmesser_oben: number;
  ist_schneide: boolean;
}

export interface Werkzeug {
  id: string;
  name: string;
  /** Optionaler eigener Zusatz, der an den Auto-Namen angehaengt wird (D34a). */
  name_zusatz?: string;
  /** Vom Backend berechneter Anzeigename (Auto-Name + Zusatz), nur lesend (D34a). */
  _anzeigename?: string;
  typ: WerkzeugTyp;
  material?: string;
  beschichtung?: string;
  durchmesser: number;
  schaft_durchmesser: number;
  schneidlaenge: number;
  gesamtlaenge: number;
  schneiden: number;
  segmente?: WerkzeugSegment[];
  halter_segmente?: WerkzeugSegment[];
  spitzenwinkel?: number | null;
  spitzenradius?: number | null;
  spitzendurchmesser?: number | null;
  max_arbeitstiefe_mm?: number | null;
  standzeit_max_minuten?: number | null;
  drehrichtung?: "cw" | "ccw";
  steigung?: "upcut" | "downcut" | "compression" | "neutral";
  notizen?: string;
}

export type MaterialKategorie =
  | "holz" | "holzwerkstoff" | "kunststoff"
  | "ne_metall" | "metall" | "sonstiges";

export interface SchnittParameterPreset {
  werkzeug_id: string;
  rpm: number;
  vorschub: number;
  plunge: number;
  stepdown: number;
  stepover_prozent: number;
}

export interface Material {
  id: string;
  name: string;
  kategorie: MaterialKategorie;
  unter_kategorie?: string;
  janka_haerte?: number | null;
  dichte?: number | null;
  schnittgeschwindigkeit_min?: number | null;
  schnittgeschwindigkeit_max?: number | null;
  presets: SchnittParameterPreset[];
  spaeneabsaugung_empfohlen?: boolean;
  risiken?: string;
  notizen?: string;
}

// --- DXF / Geometrie ---

export type GeometrieTyp =
  | "linie" | "polylinie" | "kreis" | "bogen"
  | "ellipse" | "spline" | "punkt";

export interface GeometrieObjekt {
  /** Frontend-generierte stabile ID, damit Operationen Geometrien referenzieren koennen (Master-Plan D31). */
  id?: string;
  typ: GeometrieTyp;
  layer: string;
  punkte: Array<[number, number]>;
  geschlossen: boolean;
  attribute: Record<string, unknown>;
  farbe?: number | null;
}

export interface DXFImportErgebnis {
  einheit: "mm" | "inch" | "unbekannt";
  layer: string[];
  anzahl_objekte: number;
  bounding_box: { min: [number, number]; max: [number, number] } | null;
  objekte: GeometrieObjekt[];
}

// --- Operations-Parameter ---

export type KonturSeite = "innen" | "aussen" | "auf_linie";
export type FraesRichtung = "gleichlauf" | "gegenlauf";
export type Eintauchstrategie = "senkrecht" | "rampe" | "helix";
export type TaschenStrategie =
  | "parallel" | "spiral_aussen" | "spiral_innen" | "offset_kontur" | "adaptive";
export type BohrStrategie =
  | "standard" | "peck" | "tief_peck" | "helix" | "reib";
export type GravurStrategie = "konstante_tiefe" | "v_carving";

export interface OperationParameterBasis {
  werkzeug_id: string;
  spindel_rpm: number;
  vorschub: number;
  eintauch_vorschub: number;
  sicherheitshoehe: number;
  max_tiefe: number;
  stepdown: number;
}

export interface KonturParameter extends OperationParameterBasis {
  seite: KonturSeite;
  fraes_richtung: FraesRichtung;
  eintauch_strategie: Eintauchstrategie;
  rampe_winkel_grad: number;
  tabs_anzahl: number;
  tabs_hoehe: number;
  tabs_breite: number;
  aufmass: number;
  schlichtgang: boolean;
  lead_in_laenge: number;
  lead_out_laenge: number;
}

export interface TaschenParameter extends OperationParameterBasis {
  strategie: TaschenStrategie;
  stepover_prozent: number;
  eintauch_strategie: Eintauchstrategie;
  rampe_winkel_grad: number;
  aufmass_wand: number;
  aufmass_boden: number;
  schlichtgang_wand: boolean;
  schlichtgang_boden: boolean;
  fraes_richtung: FraesRichtung;
}

export interface BohrParameter extends OperationParameterBasis {
  strategie: BohrStrategie;
  peck_tiefe: number;
  dwell_sekunden: number;
  rueckzugs_hoehe: number;
}

export interface GravurParameter extends OperationParameterBasis {
  strategie: GravurStrategie;
  spitzenwinkel_grad?: number | null;
  max_zustellung: number;
}

// --- Toolpath ---

export type BewegungsTyp = "eilgang" | "linear" | "bogen_cw" | "bogen_ccw" | "plunge";
export type OperationsTyp = "kontur" | "tasche" | "bohren" | "gravur" | "relief" | "drechseln" | "eilgang";

export type DrechselStrategie =
  | "laengs_schruppen" | "profil_schlichten" | "schrupp_und_schlicht" | "helix";

export interface WrapParameter {
  werkzeug_id: string;
  spindel_rpm: number;
  vorschub: number;
  eintauch_vorschub: number;
  sicherheitshoehe?: number;
  werkstueck_radius_mm: number;
  max_tiefe: number;
  stepdown?: number;
  geschlossen?: boolean;
  aufmass_y_mm?: number;
}

export interface DrechselParameter {
  werkzeug_id: string;
  spindel_rpm: number;
  vorschub: number;
  eintauch_vorschub: number;
  sicherheitshoehe: number;
  max_tiefe: number;
  stepdown: number;
  strategie: DrechselStrategie;
  rohmaterial_radius_mm: number;
  aufmass_schlichten_mm: number;
  schlicht_zustellung_mm: number;
  drehzahl_werkstueck_upm: number;
  profil: Array<[number, number]>;
  helix_steigung_mm_pro_umdrehung?: number;
  helix_tiefe_mm?: number;
  helix_anzahl_passes?: number;
  helix_x_start_mm?: number | null;
  helix_x_ende_mm?: number | null;
}

export interface Bewegung {
  typ: BewegungsTyp;
  x: number;
  y: number;
  z: number;
  feed?: number | null;
  i?: number | null;
  j?: number | null;
  kommentar?: string;
}

export interface Toolpath {
  operation_id: string;
  operation_typ: OperationsTyp;
  werkzeug_id: string;
  spindel_rpm: number;
  sicherheitshoehe: number;
  bewegungen: Bewegung[];
  kommentar?: string;
  metadaten?: Record<string, unknown>;
  gesamtlaenge?: number;
  schnittlaenge?: number;
}

// --- Sicherheits-Checks ---

export type CheckStufe = "info" | "warnung" | "kritisch";

export interface CheckErgebnis {
  check_id: string;
  stufe: CheckStufe;
  titel: string;
  beschreibung: string;
  bewegungs_index?: number | null;
}

export interface CheckBericht {
  hat_blocker: boolean;
  anzahl_kritisch: number;
  anzahl_warnung: number;
  ergebnisse: CheckErgebnis[];
}

// --- Postprozessoren ---

export interface RotaryProfil {
  id: string;
  name: string;
  hersteller: string;
  modell: string;
  quelle_url?: string | null;
  spannfutter_backen_anzahl: number;
  spannfutter_max_durchmesser_mm: number;
  spannfutter_min_durchmesser_mm: number;
  hat_reitstock: boolean;
  reitstock_verstellbar_mm?: number | null;
  max_werkstueck_laenge_mm: number;
  durchschiebbar: boolean;
  grbl_y_steps_pro_grad?: number | null;
  grbl_y_limit_aufheben: boolean;
  cncjs_macro_ein?: string | null;
  cncjs_macro_aus?: string | null;
  notizen: string;
}

export interface PostprozessorInfo {
  id: string;
  name: string;
  beschreibung: string;
  file_extension: string;
}

// --- Feeds & Speeds ---

export interface FeedsSpeedsErgebnis {
  rpm: number;
  vorschub: number;
  eintauch_vorschub: number;
  stepdown: number;
  stepover_prozent: number;
  schnittgeschwindigkeit_vc: number;
  spanvolumen_q: number;
  quelle: "preset" | "berechnet";
  warnungen: Array<{ stufe: CheckStufe; text: string }>;
}

// --- Operation in Liste ---

/**
 * Operation-Status (Master-Plan A48 Dependency-Graph).
 * - NEU: noch nie berechnet
 * - OK: Toolpath aktuell, Quellen gueltig
 * - DIRTY: Quelle hat sich geaendert, Recalc noetig (orange)
 * - BROKEN: Quelle fehlt - G-Code-Export blockiert (rot)
 */
export type OperationStatus = "neu" | "ok" | "dirty" | "broken";

export interface OperationEintrag {
  id: string;
  name: string;
  typ: OperationsTyp;
  /** @deprecated Nutze geometrie_ids stattdessen. */
  geometrie_id?: string | null;
  /** Geometrien die diese Operation verwendet (Master-Plan D31). */
  geometrie_ids?: string[];
  werkzeug_id: string;
  parameter: KonturParameter | TaschenParameter | BohrParameter | GravurParameter;
  toolpath?: Toolpath | null;
  sicherheits_bericht?: CheckBericht | null;
  aktiviert: boolean;
  /** A48 Dirty-Tracking. */
  status?: OperationStatus;
  fehler_text?: string;
}
