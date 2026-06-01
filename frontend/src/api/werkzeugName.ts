// Werkzeug-Anzeigename + Typ-Labels (D34a, Issue #33).
//
// Spiegelt die Backend-Logik aus `camwosa/db/werkzeug_name.py` fuer eine
// sofortige Live-Vorschau im Editor (ohne API-Roundtrip pro Tastendruck).
// Quelle der Wahrheit beim Speichern bleibt das Backend (`_anzeigename`).

import type { Werkzeug, WerkzeugTyp } from "./types";

/** Anzeige-Labels je Werkzeug-Typ (echte Umlaute). */
export const WERKZEUG_TYP_LABEL: Record<WerkzeugTyp, string> = {
  schaftfraeser: "Schaftfräser",
  kugelfraeser: "Kugelfräser",
  torusfraeser: "Torusfräser",
  v_bit: "V-Bit",
  ballnose_v_bit: "Ballnose-V-Bit",
  gravierstichel: "Gravierstichel",
  bohrer: "Bohrer",
  einschneider: "Einschneider",
  fischschwanz: "Fischschwanz",
  schruppfraeser: "Schruppfräser",
  diamantgravierer: "Diamantgravierer",
  drag_gravierer: "Schleppgravierer",
};

/** Konische Typen zeigen den Spitzenwinkel statt der Schneidenzahl. */
const KONISCH: ReadonlySet<WerkzeugTyp> = new Set<WerkzeugTyp>([
  "v_bit", "ballnose_v_bit", "gravierstichel",
  "diamantgravierer", "drag_gravierer",
]);

export function istKonisch(typ: WerkzeugTyp): boolean {
  return KONISCH.has(typ);
}

/** Durchmesser kompakt: 6 statt 6.0, 12.7 bleibt 12.7. */
function fmtMm(wert: number): string {
  if (Math.abs(wert - Math.round(wert)) < 1e-6) return String(Math.round(wert));
  return wert.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

/** Auto-Name aus den Werkzeug-Daten (ohne Zusatz). */
export function werkzeugAutoName(w: Partial<Werkzeug>): string {
  const typ = (w.typ ?? "schaftfraeser") as WerkzeugTyp;
  const teile: string[] = [WERKZEUG_TYP_LABEL[typ] ?? typ];

  if (KONISCH.has(typ) && w.spitzenwinkel != null) {
    teile.push(`${fmtMm(w.spitzenwinkel)}°`);
  }
  if (w.durchmesser != null) {
    teile.push(`Ø${fmtMm(w.durchmesser)} mm`);
  }
  if (!KONISCH.has(typ) && w.schneiden) {
    teile.push(`${w.schneiden}-Schneider`);
  }
  if (w.material) {
    teile.push(String(w.material));
  }
  return teile.join(" · ");
}

/** Voller Anzeigename: Auto-Name + optionaler Zusatz. */
export function werkzeugAnzeigename(w: Partial<Werkzeug>): string {
  const basis = werkzeugAutoName(w);
  const zusatz = (w.name_zusatz ?? "").trim();
  return zusatz ? `${basis} (${zusatz})` : basis;
}

/** Bevorzugt den Backend-Anzeigenamen, faellt sonst auf lokale Berechnung zurueck. */
export function anzeigename(w: Werkzeug): string {
  return w._anzeigename || werkzeugAnzeigename(w) || w.name || w.id;
}
