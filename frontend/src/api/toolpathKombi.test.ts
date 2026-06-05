import { describe, expect, it } from "vitest";
import { kombiniereToolpaths } from "./toolpathKombi";
import type { Toolpath } from "./types";

function tp(id: string, n: number): Toolpath {
  return {
    operation_id: id, operation_typ: "kontur", werkzeug_id: "t",
    spindel_rpm: 12000, sicherheitshoehe: 5,
    bewegungen: Array.from({ length: n }, (_, i) => ({ typ: "linear", x: i, y: 0, z: -1, feed: 800 })),
    gesamtlaenge: n, schnittlaenge: n,
  };
}

describe("kombiniereToolpaths", () => {
  it("leer -> null", () => { expect(kombiniereToolpaths([])).toBeNull(); });
  it("null/leere gefiltert", () => {
    expect(kombiniereToolpaths([null, undefined, { ...tp("a", 0) }])).toBeNull();
  });
  it("eine -> unveraendert", () => {
    const a = tp("a", 3);
    expect(kombiniereToolpaths([a])).toBe(a);
  });
  it("mehrere -> Bewegungen + Laengen summiert", () => {
    const k = kombiniereToolpaths([tp("a", 2), tp("b", 3)])!;
    expect(k.bewegungen.length).toBe(5);
    expect(k.gesamtlaenge).toBe(5);
    expect(k.schnittlaenge).toBe(5);
    expect(k.metadaten?.kombiniert_aus).toBe(2);
  });
});
