/**
 * G-Code Befehlsbibliothek (Auswahl).
 * Wird im Editor-Sidebar angezeigt, kontextbezogen passend zum Cursor.
 */

export interface GCodeBefehl {
  code: string;
  titel: string;
  beschreibung: string;
  kategorie: "bewegung" | "spindel" | "werkzeug" | "koord" | "einheit" | "ende";
  beispiel?: string;
}

export const BEFEHLE: GCodeBefehl[] = [
  // Bewegung
  { code: "G0", titel: "Eilbewegung", kategorie: "bewegung",
    beschreibung: "Bewegung ohne Materialabtrag (max. Geschwindigkeit). Niemals im Material verwenden!",
    beispiel: "G0 X100 Y50 Z5" },
  { code: "G1", titel: "Lineare Schnittbewegung", kategorie: "bewegung",
    beschreibung: "Geradlinige Bewegung mit Vorschub F.",
    beispiel: "G1 X100 Y50 Z-2 F1500" },
  { code: "G2", titel: "Kreisbogen im Uhrzeigersinn", kategorie: "bewegung",
    beschreibung: "Kreisbogen CW. I, J = relativer Mittelpunkt vom Startpunkt.",
    beispiel: "G2 X10 Y0 I5 J0 F500" },
  { code: "G3", titel: "Kreisbogen gegen Uhrzeigersinn", kategorie: "bewegung",
    beschreibung: "Kreisbogen CCW. Sonst wie G2.",
    beispiel: "G3 X10 Y0 I5 J0 F500" },

  // Koordinaten
  { code: "G17", titel: "XY-Ebene", kategorie: "koord",
    beschreibung: "Standard-Arbeitsebene fuer 3-Achs-Fraesen." },
  { code: "G18", titel: "XZ-Ebene", kategorie: "koord",
    beschreibung: "Drehmaschinen-Ebene." },
  { code: "G19", titel: "YZ-Ebene", kategorie: "koord" , beschreibung: "Selten gebraucht."},
  { code: "G54", titel: "Werkstueck-Koordinatensystem 1", kategorie: "koord",
    beschreibung: "Standard-WCS. G55-G59 fuer weitere Aufspannungen." },
  { code: "G90", titel: "Absolute Koordinaten", kategorie: "koord",
    beschreibung: "Alle Koordinaten sind absolut zum Werkstueck-Nullpunkt." },
  { code: "G91", titel: "Relative Koordinaten", kategorie: "koord",
    beschreibung: "Koordinaten sind relativ zum letzten Punkt." },

  // Einheiten
  { code: "G20", titel: "Einheiten Zoll", kategorie: "einheit",
    beschreibung: "CAMWOSA arbeitet in mm — G20 sollte nicht im Output sein!" },
  { code: "G21", titel: "Einheiten Millimeter", kategorie: "einheit",
    beschreibung: "Standard fuer CAMWOSA." },
  { code: "G94", titel: "Vorschub mm/min", kategorie: "einheit",
    beschreibung: "Standard. F-Wert ist mm/min." },
  { code: "G95", titel: "Vorschub mm/Umdrehung", kategorie: "einheit",
    beschreibung: "Drehmaschinen-Modus." },

  // Spindel
  { code: "M3", titel: "Spindel ein (CW)", kategorie: "spindel",
    beschreibung: "Spindel im Uhrzeigersinn. S = Drehzahl in RPM.",
    beispiel: "M3 S18000" },
  { code: "M4", titel: "Spindel ein (CCW)", kategorie: "spindel",
    beschreibung: "Spindel gegen Uhrzeigersinn. Selten beim Fraesen." },
  { code: "M5", titel: "Spindel aus", kategorie: "spindel" , beschreibung: "Spindel stoppt."},

  // Werkzeug / Pause
  { code: "M0", titel: "Programm-Pause", kategorie: "werkzeug",
    beschreibung: "Maschine haelt an, wartet auf Continue. CAMWOSA nutzt das fuer Werkzeugwechsel." },
  { code: "M6", titel: "Werkzeugwechsel", kategorie: "werkzeug",
    beschreibung: "GRBL unterstuetzt M6 nicht — CAMWOSA nutzt M0 stattdessen." },

  // Bohrzyklen
  { code: "G81", titel: "Standard-Bohrzyklus", kategorie: "bewegung",
    beschreibung: "Bohren bis Z, dann Rueckzug. GRBL unterstuetzt G81 nicht." },
  { code: "G82", titel: "Bohrzyklus mit Verweildauer", kategorie: "bewegung",
    beschreibung: "Wie G81 mit Pause am Bohrgrund." },
  { code: "G83", titel: "Tief-Bohrzyklus (Spanbrechen)", kategorie: "bewegung",
    beschreibung: "Pecking — schrittweise mit Rueckzug. GRBL unterstuetzt G83 nicht." },

  // Programm-Ende
  { code: "M30", titel: "Programm-Ende + Rewind", kategorie: "ende",
    beschreibung: "Beendet das Programm und faehrt zurueck zum Anfang." },
  { code: "M2", titel: "Programm-Ende", kategorie: "ende",
    beschreibung: "Beendet das Programm." },
];

export function findeBefehl(zeile: string): GCodeBefehl | null {
  const m = zeile.trim().match(/^([GM]\d+)/i);
  if (!m) return null;
  const code = m[1].toUpperCase();
  return BEFEHLE.find((b) => b.code === code) ?? null;
}
