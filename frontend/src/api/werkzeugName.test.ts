/**
 * Tests fuer den Werkzeug-Auto-Namen (D34a) — Spiegel der Backend-Logik.
 */

import { describe, expect, it } from "vitest";
import { werkzeugAutoName, werkzeugAnzeigename, anzeigename } from "./werkzeugName";
import type { Werkzeug } from "./types";

function wz(over: Partial<Werkzeug> = {}): Werkzeug {
  return {
    id: "t", name: "", typ: "schaftfraeser", durchmesser: 6,
    schaft_durchmesser: 6, schneidlaenge: 12, gesamtlaenge: 40, schneiden: 2,
    ...over,
  };
}

describe("werkzeugAutoName", () => {
  it("baut Schaftfraeser-Name aus Daten", () => {
    const n = werkzeugAutoName(wz({ durchmesser: 6, schneiden: 2 }));
    expect(n).toContain("Schaftfräser");
    expect(n).toContain("Ø6 mm");
    expect(n).toContain("2-Schneider");
  });

  it("formatiert Ganzzahl ohne Nachkomma", () => {
    expect(werkzeugAutoName(wz({ durchmesser: 3 }))).toContain("Ø3 mm");
    expect(werkzeugAutoName(wz({ durchmesser: 3 }))).not.toContain("3.0");
  });

  it("behaelt Nachkomma bei krummem Durchmesser", () => {
    expect(werkzeugAutoName(wz({ durchmesser: 12.7 }))).toContain("Ø12.7 mm");
  });

  it("zeigt bei V-Bit den Winkel statt Schneiden", () => {
    const n = werkzeugAutoName(wz({ typ: "v_bit", durchmesser: 12.7, spitzenwinkel: 60 }));
    expect(n).toContain("V-Bit");
    expect(n).toContain("60°");
    expect(n).not.toContain("Schneider");
  });

  it("nimmt Material in den Namen auf", () => {
    expect(werkzeugAutoName(wz({ material: "Hartmetall" }))).toContain("Hartmetall");
  });
});

describe("werkzeugAnzeigename", () => {
  it("ohne Zusatz == Auto-Name", () => {
    const w = wz();
    expect(werkzeugAnzeigename(w)).toBe(werkzeugAutoName(w));
  });

  it("haengt Zusatz in Klammern an", () => {
    const w = wz({ name_zusatz: "mein Liebling" });
    expect(werkzeugAnzeigename(w)).toContain("(mein Liebling)");
  });

  it("ignoriert leeren Zusatz", () => {
    expect(werkzeugAnzeigename(wz({ name_zusatz: "   " }))).not.toContain("(");
  });
});

describe("anzeigename", () => {
  it("bevorzugt den Backend-Anzeigenamen", () => {
    expect(anzeigename(wz({ _anzeigename: "Vom Backend" }))).toBe("Vom Backend");
  });

  it("faellt auf lokale Berechnung zurueck", () => {
    expect(anzeigename(wz())).toContain("Schaftfräser");
  });
});
