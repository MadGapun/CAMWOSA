/**
 * Tests fuer die Frontend-Zeitschaetzung (K5) — Spiegel von zeit_schaetzung.py.
 */

import { describe, expect, it } from "vitest";
import { formatiereDauer, schaetzeToolpathZeit } from "./zeit";
import type { Toolpath } from "./types";

function tp(bew: Toolpath["bewegungen"]): Toolpath {
  return {
    operation_id: "op", operation_typ: "kontur", werkzeug_id: "t",
    spindel_rpm: 12000, sicherheitshoehe: 5, bewegungen: bew,
  };
}

describe("formatiereDauer", () => {
  it("kurze Dauer mit Sekunden", () => {
    expect(formatiereDauer(72)).toBe("1 Min 12 Sek");
  });
  it("Stunden + Minuten ohne Sekunden", () => {
    expect(formatiereDauer(3 * 3600 + 5 * 60 + 9)).toBe("3 Std 5 Min");
  });
  it("unter 1 Sekunde", () => {
    expect(formatiereDauer(0.4)).toBe("unter 1 Sek");
  });
});

describe("schaetzeToolpathZeit", () => {
  it("Schnitt: 600 mm @ 600 mm/min = 60 s (ohne Overhead)", () => {
    const z = schaetzeToolpathZeit(
      tp([
        { typ: "linear", x: 0, y: 0, z: -1, feed: 600 },
        { typ: "linear", x: 600, y: 0, z: -1, feed: 600 },
      ]),
      { eilgangMmMin: 3000, overheadFaktor: 1.0 },
    );
    expect(z.schnitt_sekunden).toBeCloseTo(60, 1);
    expect(z.eilgang_sekunden).toBeCloseTo(0, 5);
  });

  it("Eilgang separat gezaehlt", () => {
    const z = schaetzeToolpathZeit(
      tp([
        { typ: "eilgang", x: 0, y: 0, z: 5 },
        { typ: "eilgang", x: 3000, y: 0, z: 5 },
      ]),
      { eilgangMmMin: 3000, overheadFaktor: 1.0 },
    );
    expect(z.eilgang_sekunden).toBeCloseTo(60, 1);
    expect(z.schnitt_sekunden).toBeCloseTo(0, 5);
  });

  it("Overhead-Faktor wird angewendet", () => {
    const z = schaetzeToolpathZeit(
      tp([
        { typ: "linear", x: 0, y: 0, z: -1, feed: 600 },
        { typ: "linear", x: 600, y: 0, z: -1, feed: 600 },
      ]),
      { eilgangMmMin: 3000, overheadFaktor: 1.15 },
    );
    expect(z.gesamt_sekunden).toBeCloseTo(69, 0);
  });
});
