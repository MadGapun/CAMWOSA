/**
 * Zentrale Sammlung der CAM-Fachbegriffe + Erklaerungen.
 *
 * Wird vom <FachTooltip>-Komponenten benutzt. So bleibt die Erklaerung
 * konsistent ueber alle Views — und wenn ein Begriff besser erklaert wird,
 * profitieren alle Stellen.
 */

import type { FachTooltip } from "./Tooltip";

type FachDefinition = Omit<Parameters<typeof FachTooltip>[0], "begriff">;

export const FACHBEGRIFFE: Record<string, FachDefinition & { begriff: string }> = {
  stepdown: {
    begriff: "Stepdown",
    definition:
      "Wie viel Material pro Z-Pass abgetragen wird. Tiefe Operationen werden in mehreren Schichten gefraest.",
    formel: "stepdown ≤ 0.5 × Werkzeug-Durchmesser (Hartholz)",
    hinweis:
      "Zu hoher Wert → Werkzeug-Bruch oder schlechte Oberflaeche. Bei sproeden Materialien defensiv waehlen.",
  },
  stepover: {
    begriff: "Stepover",
    definition:
      "Seitlicher Versatz zwischen benachbarten Bahnen — in Prozent vom Werkzeug-Durchmesser.",
    formel: "Holz: 30–50 % · Kunststoff: 40–60 % · Metall: 10–30 %",
    hinweis:
      "Hoher Wert = schneller, aber mehr Stufen. Bei Schlichtgang auf 15–25 % runter.",
  },
  vorschub: {
    begriff: "Vorschub (F)",
    definition:
      "Geschwindigkeit mit der das Werkzeug seitlich durch das Material faehrt (mm/min).",
    formel: "F = Zahnvorschub × Zaehnezahl × RPM",
    hinweis: "Zu hoch → Werkzeug-Bruch · Zu niedrig → Reiben statt Schneiden, Hitze.",
  },
  plunge: {
    begriff: "Plunge / Eintauch-Vorschub",
    definition:
      "Vorschub-Geschwindigkeit beim senkrechten Eintauchen in das Material (mm/min).",
    formel: "Typisch 1/3 des Normal-Vorschubs",
    hinweis:
      "Senkrechtes Eintauchen ist hart. Besser ist Rampe oder Helix-Eintauchen.",
  },
  spanlast: {
    begriff: "Spanlast (Chipload)",
    definition:
      "Dicke des Spans pro Zahn pro Umdrehung. Bestimmt ob das Werkzeug effizient schneidet.",
    formel: "Chipload = Vorschub / (RPM × Zaehnezahl)",
    hinweis: "Zu klein = Reiben + Hitze + Standzeit kurz. Material-spezifisch.",
  },
  rampe: {
    begriff: "Rampen-Eintauchen",
    definition:
      "Das Werkzeug taucht schraeg in das Material ein (z.B. 3-15°), statt senkrecht.",
    hinweis:
      "Schonender als Plunge — besonders bei Hartmetall-Fraesern und harten Materialien.",
  },
  helix_eintauchen: {
    begriff: "Helix-Eintauchen",
    definition:
      "Das Werkzeug spiralt sich in einer Schraubenbewegung in das Material — ideal fuer Taschen.",
    hinweis: "Sicherster Eintauchmodus, aber braucht Platz fuer den Spiral-Radius.",
  },
  tabs: {
    begriff: "Tabs (Haltestege)",
    definition:
      "Kleine Material-Bruecken die ein ausgeschnittenes Teil im Rohmaterial halten, bis das Programm fertig ist.",
    hinweis:
      "Ohne Tabs faellt das Teil im letzten Pass weg → Werkzeug-Schaden moeglich.",
  },
  aufmass: {
    begriff: "Aufmass",
    definition:
      "Material das nach dem Schruppen stehen bleibt — wird vom Schlichtgang sauber abgetragen.",
    formel: "Typisch 0.2–0.5 mm",
  },
  adaptive_clearing: {
    begriff: "Adaptive Clearing (Trochoidal)",
    definition:
      "Schruppstrategie die mit gleichbleibender Werkzeug-Belastung arbeitet — kleine kreisende Bewegungen.",
    hinweis:
      "Werkzeug-schonend und schnell, aber rechen-intensiv. Lohnt sich bei tiefen Taschen.",
  },
  schnittgeschwindigkeit: {
    begriff: "Schnittgeschwindigkeit (Vc)",
    definition:
      "Geschwindigkeit mit der die Werkzeug-Schneide das Material kreuzt (m/min).",
    formel: "Vc = π × Werkzeug-Ø × RPM / 1000",
    hinweis: "Material-spezifisch — Holz: 300–600 m/min, Aluminium: 200–500.",
  },
  drechseln_drehzahl: {
    begriff: "Werkstueck-Drehzahl (Rotary)",
    definition:
      "Wie schnell sich das Werkstueck im Rotary-Aufsatz dreht. Nicht zu verwechseln mit der Spindel-RPM des Fraesers.",
    formel: "Helix-Steigung × Drehzahl = X-Vorschub",
    hinweis:
      "Zu hoch → Werkstueck fliegt aus dem Spannfutter. Zu niedrig → schlechte Oberflaeche.",
  },
};
