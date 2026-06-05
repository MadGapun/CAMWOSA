/**
 * Smoke-Tests fuer die neuen erklaerenden Piktogramme (Cluster Q4/Q5).
 * Render via renderToStaticMarkup (kein DOM noetig), analog WerkzeugGrafik.test.
 */

import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import OperationGrafik from "./OperationGrafik";
import StrategieGrafik from "./StrategieGrafik";
import KonturSeiteGrafik from "./KonturSeiteGrafik";
import type { OperationsTyp } from "../api/types";

describe("OperationGrafik", () => {
  const typen: OperationsTyp[] = ["kontur", "tasche", "bohren", "gravur", "relief"];
  it("rendert SVG mit Pfad fuer jeden Operations-Typ", () => {
    for (const typ of typen) {
      const html = renderToStaticMarkup(<OperationGrafik typ={typ} />);
      expect(html, typ).toContain("<svg");
    }
  });
});

describe("StrategieGrafik", () => {
  it("rendert Tasche-Strategien", () => {
    for (const w of ["parallel", "spiral_aussen", "offset_kontur", "adaptive"]) {
      const html = renderToStaticMarkup(<StrategieGrafik art="tasche" wert={w} />);
      expect(html, w).toContain("<svg");
    }
  });
  it("rendert Eintauch-Strategien", () => {
    for (const w of ["senkrecht", "rampe", "helix"]) {
      const html = renderToStaticMarkup(<StrategieGrafik art="eintauchen" wert={w} />);
      expect(html, w).toContain("<svg");
    }
  });
});

describe("KonturSeiteGrafik", () => {
  it("rendert Seite + Tabs", () => {
    const html = renderToStaticMarkup(
      <KonturSeiteGrafik seite="aussen" tabsAnzahl={3} zeige="beide" />,
    );
    expect(html).toContain("<svg");
  });
});
