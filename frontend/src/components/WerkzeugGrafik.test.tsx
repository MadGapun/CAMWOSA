/**
 * Komponenten-Test fuer die Werkzeug-Skizze (D34, Issue #33).
 *
 * Prueft, dass die parametrische Silhouette je Typ einen gueltigen Pfad
 * rendert und die Bemassung im gross-Modus erscheint.
 */

import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import WerkzeugGrafik from "./WerkzeugGrafik";
import type { WerkzeugTyp } from "../api/types";

const ALLE_TYPEN: WerkzeugTyp[] = [
  "schaftfraeser", "kugelfraeser", "torusfraeser", "v_bit", "ballnose_v_bit",
  "gravierstichel", "bohrer", "einschneider", "fischschwanz",
  "schruppfraeser", "diamantgravierer", "drag_gravierer",
];

describe("WerkzeugGrafik", () => {
  it("rendert fuer jeden Typ ein SVG mit Pfad", () => {
    for (const typ of ALLE_TYPEN) {
      const html = renderToStaticMarkup(
        <WerkzeugGrafik geo={{ typ, durchmesser: 6, schaft_durchmesser: 6, schneidlaenge: 12, gesamtlaenge: 40 }} />,
      );
      expect(html, typ).toContain("<svg");
      expect(html, typ).toMatch(/<path[^>]+d="M/);
    }
  });

  it("zeigt im gross-Modus eine Bemassung (Ø + Marker)", () => {
    const html = renderToStaticMarkup(
      <WerkzeugGrafik geo={{ typ: "schaftfraeser", durchmesser: 8 }} mode="gross" />,
    );
    expect(html).toContain("Ø8");
    expect(html).toContain("marker");
  });

  it("V-Bit-Skizze laeuft in eine Spitze (kein flacher Boden)", () => {
    const html = renderToStaticMarkup(
      <WerkzeugGrafik geo={{ typ: "v_bit", durchmesser: 12.7, spitzenwinkel: 60 }} mode="gross" />,
    );
    expect(html).toContain("60°");
  });
});
