// Kombiniert mehrere Toolpaths zu einem (Cluster Q3): eine Operation kann mehrere
// Geometrien bearbeiten — je Geometrie ein Toolpath, danach zu einem zusammengefasst.
//
// Jeder Einzel-Toolpath beginnt mit Anfahrt auf Sicherheitshoehe + Plunge, daher ist
// das blosse Aneinanderhaengen der Bewegungen sicher (das Werkzeug zieht zwischen den
// Geometrien hoch). Die Fahrweg-Optimierung (J9) kann die Reihenfolge spaeter straffen.

import type { Toolpath } from "./types";

export function kombiniereToolpaths(tps: Array<Toolpath | null | undefined>): Toolpath | null {
  const valid = tps.filter((t): t is Toolpath => !!t && t.bewegungen.length > 0);
  if (valid.length === 0) return null;
  if (valid.length === 1) return valid[0];
  const erste = valid[0];
  return {
    ...erste,
    bewegungen: valid.flatMap((t) => t.bewegungen),
    gesamtlaenge: valid.reduce((s, t) => s + (t.gesamtlaenge ?? 0), 0),
    schnittlaenge: valid.reduce((s, t) => s + (t.schnittlaenge ?? 0), 0),
    metadaten: { ...(erste.metadaten ?? {}), kombiniert_aus: valid.length },
  };
}
