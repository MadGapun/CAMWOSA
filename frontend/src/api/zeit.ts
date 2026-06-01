// Bearbeitungszeit-Schaetzung im Frontend (K5, Issue #47).
//
// Spiegelt `camwosa/gcode/zeit_schaetzung.py` fuer eine sofortige Live-Anzeige.
// Summiert ueber die tatsaechlichen Bewegungs-Feeds → reflektiert automatisch
// die Vorschub-Anpassung (J11) und optimierte Fahrwege (J9/J10), sobald sie im
// Toolpath stecken. Bewusst eine Schaetzung (Groessenordnung, nicht Sekunde).

import type { Toolpath } from "./types";

export interface ZeitSchaetzung {
  schnitt_sekunden: number;
  eilgang_sekunden: number;
  gesamt_sekunden: number;
}

/** Sekunden → kompakter deutscher Klartext, z.B. „1 Std 23 Min" / „4 Min 12 Sek". */
export function formatiereDauer(sekunden: number): string {
  if (sekunden < 1) return "unter 1 Sek";
  const s = Math.round(sekunden);
  const std = Math.floor(s / 3600);
  const minuten = Math.floor((s % 3600) / 60);
  const sek = s % 60;
  const teile: string[] = [];
  if (std) teile.push(`${std} Std`);
  if (minuten) teile.push(`${minuten} Min`);
  if (sek && std === 0 && minuten < 10) teile.push(`${sek} Sek`);
  if (teile.length === 0) teile.push(`${sek} Sek`);
  return teile.join(" ");
}

/** Schaetzt die Zeit eines Toolpaths, Schnitt/Eilgang getrennt (mit Overhead). */
export function schaetzeToolpathZeit(
  toolpath: Toolpath,
  opt: {
    eilgangMmMin: number;
    overheadFaktor?: number;
    fallbackVorschubMmMin?: number;
  },
): ZeitSchaetzung {
  const eil = opt.eilgangMmMin > 0 ? opt.eilgangMmMin : 3000;
  const overhead = opt.overheadFaktor ?? 1.15;
  const fallback = opt.fallbackVorschubMmMin ?? 1000;

  let schnittMin = 0;
  let eilgangMin = 0;
  const bew = toolpath.bewegungen;
  for (let i = 1; i < bew.length; i++) {
    const a = bew[i - 1];
    const b = bew[i];
    const d = Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
    if (b.typ === "eilgang") {
      eilgangMin += d / eil;
    } else {
      schnittMin += d / (b.feed || fallback);
    }
  }
  const schnitt = schnittMin * 60 * overhead;
  const eilgang = eilgangMin * 60 * overhead;
  return {
    schnitt_sekunden: schnitt,
    eilgang_sekunden: eilgang,
    gesamt_sekunden: schnitt + eilgang,
  };
}
