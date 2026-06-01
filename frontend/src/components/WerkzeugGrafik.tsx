// Werkzeug-Grafik: typ-abhaengige SVG-Skizze (D34/D37, Issue #33).
//
// Markus' Anforderung: beim Anlegen eines Fraesers eine erklaerende Grafik je
// Typ (wie die Geometrie aussieht), und in der Auswahl/Liste dieselbe Grafik
// verkleinert als Piktogramm.
//
// - mode="piktogramm": kleine Silhouette ohne Beschriftung (Listen/Dropdowns)
// - mode="gross":      grosse, bemasste Skizze mit Highlight bei Feld-Fokus
//
// Die Silhouette ist stilisiert (gut erkennbar), nicht massstabsgetreu — die
// relativen Durchmesser (Schaft vs. Schneide) und die Spitzenform je Typ
// werden aber korrekt dargestellt.

import type { WerkzeugTyp } from "../api/types";

export type GrafikGeo = {
  typ: WerkzeugTyp;
  durchmesser?: number;
  schaft_durchmesser?: number;
  schneidlaenge?: number;
  gesamtlaenge?: number;
  spitzenwinkel?: number | null;
  spitzendurchmesser?: number | null;
  spitzenradius?: number | null;
};

export type MassFeld =
  | "durchmesser" | "schaft_durchmesser" | "schneidlaenge"
  | "gesamtlaenge" | "spitzenwinkel" | "spitzendurchmesser";

interface Props {
  geo: GrafikGeo;
  mode?: "piktogramm" | "gross";
  highlight?: MassFeld | null;
  className?: string;
  size?: number; // Pixel-Kante fuer Piktogramm
}

const W = 64;
const H = 96;
const CX = W / 2;
const TOP = 6;
const BOT = 90;
const USABLE = BOT - TOP;
const MAXHALF = 21;

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

const KONISCH = new Set<WerkzeugTyp>([
  "v_bit", "ballnose_v_bit", "gravierstichel", "diamantgravierer", "drag_gravierer",
]);

/** Rechnet die Schluessel-Geometrie der Skizze aus den Werkzeug-Massen. */
function layout(geo: GrafikGeo) {
  const d = geo.durchmesser ?? 6;
  const ds = geo.schaft_durchmesser ?? d;
  const maxD = Math.max(d, ds, 0.1);
  const scale = MAXHALF / maxD;
  const cutHalf = clamp((d / 2) * scale, 2.5, MAXHALF);
  const shankHalf = clamp((ds / 2) * scale, 2.5, MAXHALF);

  const prop = clamp(
    (geo.schneidlaenge ?? 0) > 0 && (geo.gesamtlaenge ?? 0) > 0
      ? geo.schneidlaenge! / geo.gesamtlaenge!
      : 0.42,
    0.22, 0.62,
  );
  const cutH = prop * USABLE;
  const yCutTop = BOT - cutH;
  return { cutHalf, shankHalf, yCutTop, cutH };
}

/** Geschlossener Pfad der Werkzeug-Silhouette (symmetrisch um CX). */
function silhouette(geo: GrafikGeo): string {
  const { cutHalf, shankHalf, yCutTop } = layout(geo);
  const t = geo.typ;
  const lShank = CX - shankHalf;
  const rShank = CX + shankHalf;
  const lCut = CX - cutHalf;
  const rCut = CX + cutHalf;

  // gemeinsamer Kopf: Schaft von oben bis Schneid-Beginn (linke Seite)
  const head = `M ${lShank} ${TOP} L ${lShank} ${yCutTop} L ${lCut} ${yCutTop}`;
  // gemeinsamer Schwanz: rechte Seite zurueck nach oben
  const tail = `L ${rCut} ${yCutTop} L ${rShank} ${yCutTop} L ${rShank} ${TOP} Z`;

  if (t === "kugelfraeser") {
    const r = cutHalf;
    return `${head} L ${lCut} ${BOT - r} A ${r} ${r} 0 0 0 ${rCut} ${BOT - r} ${tail}`;
  }
  if (t === "torusfraeser") {
    const r = clamp((geo.spitzenradius ?? cutHalf * 0.45) * (MAXHALF / Math.max(geo.durchmesser ?? 6, 0.1)), 2, cutHalf - 0.5);
    return `${head} L ${lCut} ${BOT - r} A ${r} ${r} 0 0 0 ${lCut + r} ${BOT}`
      + ` L ${rCut - r} ${BOT} A ${r} ${r} 0 0 0 ${rCut} ${BOT - r} ${tail}`;
  }
  if (t === "fischschwanz") {
    // flacher Boden mit kleiner Mittenspitze nach unten
    return `${head} L ${lCut} ${BOT - 5} L ${CX} ${BOT} L ${rCut} ${BOT - 5} ${tail}`;
  }
  if (t === "bohrer") {
    // 118°-Spitze (Punkthoehe ~ 0.6 * Halbdurchmesser)
    const ph = cutHalf * 0.62;
    return `${head} L ${lCut} ${BOT - ph} L ${CX} ${BOT} L ${rCut} ${BOT - ph} ${tail}`;
  }
  if (KONISCH.has(t)) {
    // Kegel: von Schneid-Ø oben zur Spitze. Optional kleiner Flachtipp.
    const tipHalf = clamp(((geo.spitzendurchmesser ?? 0) / 2) * (MAXHALF / Math.max(geo.durchmesser ?? 6, 0.1)), 0, cutHalf - 0.5);
    if (t === "ballnose_v_bit") {
      const br = Math.max(tipHalf, 2.2);
      return `${head} L ${CX - br} ${BOT - br} A ${br} ${br} 0 0 0 ${CX + br} ${BOT - br} ${tail}`;
    }
    if (tipHalf > 0.2) {
      return `${head} L ${CX - tipHalf} ${BOT} L ${CX + tipHalf} ${BOT} ${tail}`;
    }
    return `${head} L ${CX} ${BOT} ${tail}`;
  }
  // schaftfraeser / einschneider / schruppfraeser: flacher Boden
  return `${head} L ${lCut} ${BOT} L ${rCut} ${BOT} ${tail}`;
}

/** Dekorative Innen-Linien (Schneiden-Andeutung). */
function flutes(geo: GrafikGeo): JSX.Element | null {
  const { cutHalf, yCutTop } = layout(geo);
  const t = geo.typ;
  if (KONISCH.has(t) || t === "bohrer") {
    if (t === "bohrer") {
      return (
        <g stroke="currentColor" strokeWidth={1} opacity={0.35} fill="none">
          <path d={`M ${CX - cutHalf + 1} ${yCutTop + 2} Q ${CX} ${yCutTop + 14} ${CX - cutHalf + 1} ${BOT - 8}`} />
          <path d={`M ${CX + cutHalf - 1} ${yCutTop + 2} Q ${CX} ${yCutTop + 14} ${CX + cutHalf - 1} ${BOT - 8}`} />
        </g>
      );
    }
    return null;
  }
  if (t === "schruppfraeser") {
    // Maiskolben-Andeutung: horizontale Kerben auf der Schneide
    const ys = [0.25, 0.45, 0.65, 0.85].map((f) => yCutTop + f * (BOT - yCutTop));
    return (
      <g stroke="currentColor" strokeWidth={1} opacity={0.4} fill="none">
        {ys.map((y, i) => (
          <line key={i} x1={CX - cutHalf} y1={y} x2={CX + cutHalf} y2={y + 2.5} />
        ))}
      </g>
    );
  }
  // Standard-Fraeser: zwei schraege Spirallinien
  return (
    <g stroke="currentColor" strokeWidth={1} opacity={0.35} fill="none">
      <line x1={CX - cutHalf} y1={yCutTop + 3} x2={CX + cutHalf} y2={BOT - 4} />
      <line x1={CX - cutHalf} y1={yCutTop + (BOT - yCutTop) * 0.5} x2={CX + cutHalf} y2={BOT - 2} />
    </g>
  );
}

/** Bemassung mit Highlight (nur gross-Modus). */
function masse(geo: GrafikGeo, highlight: MassFeld | null | undefined): JSX.Element {
  const { cutHalf, shankHalf, yCutTop } = layout(geo);
  const acc = "var(--camwosa-accent, #38bdf8)";
  const mut = "currentColor";
  const col = (f: MassFeld) => (highlight === f ? acc : mut);
  const op = (f: MassFeld) => (highlight === f ? 1 : 0.45);
  const sw = (f: MassFeld) => (highlight === f ? 1.6 : 1);

  return (
    <g fontSize={7} fontFamily="ui-monospace, monospace">
      {/* Schneid-Ø unten */}
      <g stroke={col("durchmesser")} strokeWidth={sw("durchmesser")} opacity={op("durchmesser")}>
        <line x1={CX - cutHalf} y1={BOT + 5} x2={CX + cutHalf} y2={BOT + 5} markerEnd="url(#wz-arr)" markerStart="url(#wz-arr)" />
      </g>
      <text x={CX} y={BOT + 12} fill={col("durchmesser")} opacity={op("durchmesser")} textAnchor="middle">
        Ø{geo.durchmesser ?? "?"}
      </text>

      {/* Schaft-Ø oben */}
      <g stroke={col("schaft_durchmesser")} strokeWidth={sw("schaft_durchmesser")} opacity={op("schaft_durchmesser")}>
        <line x1={CX - shankHalf} y1={TOP - 2} x2={CX + shankHalf} y2={TOP - 2} markerEnd="url(#wz-arr)" markerStart="url(#wz-arr)" />
      </g>

      {/* Schneidlaenge rechts */}
      <g stroke={col("schneidlaenge")} strokeWidth={sw("schneidlaenge")} opacity={op("schneidlaenge")}>
        <line x1={W - 4} y1={yCutTop} x2={W - 4} y2={BOT} markerEnd="url(#wz-arr)" markerStart="url(#wz-arr)" />
      </g>

      {/* Spitzenwinkel (nur konisch) */}
      {KONISCH.has(geo.typ) && geo.spitzenwinkel != null && (
        <text x={CX + 3} y={BOT - 6} fill={col("spitzenwinkel")} opacity={op("spitzenwinkel")} textAnchor="start">
          {geo.spitzenwinkel}°
        </text>
      )}
    </g>
  );
}

export default function WerkzeugGrafik({
  geo, mode = "piktogramm", highlight, className, size,
}: Props) {
  const px = size ?? (mode === "gross" ? 150 : 28);
  const pad = mode === "gross" ? 16 : 0;
  const vb = `${-pad} ${-pad} ${W + 2 * pad} ${H + 2 * pad}`;

  return (
    <svg
      viewBox={vb}
      width={px}
      height={(px * (H + 2 * pad)) / (W + 2 * pad)}
      className={className}
      role="img"
      aria-label={`Werkzeug-Skizze ${geo.typ}`}
    >
      <defs>
        <marker id="wz-arr" markerWidth={5} markerHeight={5} refX={2.5} refY={2.5} orient="auto">
          <path d="M0,0 L5,2.5 L0,5 Z" fill="currentColor" />
        </marker>
      </defs>
      <path d={silhouette(geo)} fill="currentColor" fillOpacity={0.14} stroke="currentColor" strokeWidth={mode === "gross" ? 1.5 : 2} strokeLinejoin="round" />
      {flutes(geo)}
      {mode === "gross" && masse(geo, highlight)}
    </svg>
  );
}
