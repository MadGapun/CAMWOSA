// Strategie-Grafik: erklaerende SVG-Piktogramme fuer CAM-Strategien.
//
// Analog zu WerkzeugGrafik (D34/D37) — Markus' Anforderung: zu jeder
// auswaehlbaren Strategie ein kleines, sofort verstaendliches Bild, sowohl
// im Dropdown/in der Liste (klein) als auch gross neben dem Auswahlfeld.
//
// Abgedeckt:
//   art="tasche":     parallel (Zickzack), spiral_aussen, spiral_innen,
//                     offset_kontur, adaptive (trochoidal)
//   art="eintauchen": senkrecht, rampe, helix
//
// Die Werte entsprechen exakt den String-Literalen aus ../api/types
// (TaschenStrategie, Eintauchstrategie). Reines SVG, nur currentColor — die
// Farbe kommt also vom umgebenden Text/Theme. Keine externen Abhaengigkeiten.

import type { TaschenStrategie, Eintauchstrategie } from "../api/types";

export type StrategieArt = "tasche" | "eintauchen";

interface Props {
  art: StrategieArt;
  wert: TaschenStrategie | Eintauchstrategie | string;
  mode?: "piktogramm" | "gross";
  className?: string;
  size?: number; // Pixel-Kante (quadratisch)
  title?: string; // optionaler aria-/Tooltip-Text (Default: generiert)
}

// Quadratisches Koordinatensystem fuer alle Piktogramme.
const VB = 64;
const PAD = 7;
const A = PAD; // linke/obere Kante des Nutzbereichs
const B = VB - PAD; // rechte/untere Kante
const SPAN = B - A;
const MID = VB / 2;

// Gemeinsame Stil-Konstanten (Fuellung dezent wie bei WerkzeugGrafik).
const FILL_OP = 0.1;
const GHOST_OP = 0.28; // Rohteil-/Materialkante
const PATH_OP = 0.92; // Werkzeugbahn

function fmt(n: number): string {
  // kompakte, deterministische Pfad-Zahlen (keine Float-Artefakte im DOM)
  return Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/\.?0+$/, "");
}

// ---------------------------------------------------------------------------
// Bahn-Generatoren (liefern reine SVG-Pfad-d-Strings)
// ---------------------------------------------------------------------------

/** Boustrophedon-Zickzack: parallele Bahnen, an den Enden verbunden. */
function zickzackPfad(reihen = 5): string {
  const stepY = SPAN / (reihen - 1);
  const parts: string[] = [];
  for (let i = 0; i < reihen; i++) {
    const y = fmt(A + i * stepY);
    const linksZuerst = i % 2 === 0;
    const x1 = fmt(linksZuerst ? A : B);
    const x2 = fmt(linksZuerst ? B : A);
    parts.push(i === 0 ? `M ${x1} ${y}` : `L ${x1} ${y}`);
    parts.push(`L ${x2} ${y}`);
  }
  return parts.join(" ");
}

/**
 * Archimedische Spirale als Polylinie um das Zentrum.
 * richtung="ein": startet aussen (grosser Radius), endet im Zentrum.
 * richtung="aus": startet im Zentrum, endet aussen.
 */
function spiralePfad(richtung: "ein" | "aus"): {
  d: string;
  start: [number, number];
  startTangente: [number, number];
} {
  const rMax = SPAN / 2 - 1;
  const windungen = 2.6;
  const thetaMax = windungen * 2 * Math.PI;
  const schritte = 80;
  const pts: Array<[number, number]> = [];
  for (let i = 0; i <= schritte; i++) {
    const f = i / schritte; // 0..1 vom Zentrum nach aussen
    const theta = f * thetaMax;
    const r = f * rMax;
    pts.push([MID + r * Math.cos(theta), MID + r * Math.sin(theta)]);
  }
  const reihe = richtung === "aus" ? pts : [...pts].reverse();
  const d = reihe
    .map((p, i) => `${i === 0 ? "M" : "L"} ${fmt(p[0])} ${fmt(p[1])}`)
    .join(" ");
  const start = reihe[0];
  const next = reihe[1] ?? reihe[0];
  return { d, start, startTangente: [next[0] - start[0], next[1] - start[1]] };
}

/** Konzentrische, abgerundete Rechteck-Konturen (offset_kontur). */
function offsetKonturen(): Array<{ x: number; y: number; w: number; h: number; r: number }> {
  const ringe = 4;
  const stepX = (SPAN / 2) / ringe;
  const out: Array<{ x: number; y: number; w: number; h: number; r: number }> = [];
  for (let i = 0; i < ringe; i++) {
    const off = i * stepX;
    out.push({
      x: A + off,
      y: A + off,
      w: SPAN - 2 * off,
      h: SPAN - 2 * off,
      r: Math.max(2, 7 - i * 1.5),
    });
  }
  return out;
}

/**
 * Trochoidale (adaptive) Bahn: ueberlappende Schlaufen, die nach rechts
 * fortschreiten — wie Adaptive Clearing es erzeugt.
 */
function trochoidPfad(): string {
  const schleifen = 3;
  const loopR = SPAN / (schleifen * 2 + 1);
  const vorschub = (SPAN - 2 * loopR) / schleifen;
  const schritte = 120;
  const pts: Array<[number, number]> = [];
  for (let i = 0; i <= schritte; i++) {
    const f = i / schritte;
    const theta = f * schleifen * 2 * Math.PI;
    const cx = A + loopR + f * (SPAN - 2 * loopR);
    const x = cx + loopR * 0.55 * Math.cos(theta) - (vorschub / (2 * Math.PI)) * 0;
    const y = MID + loopR * Math.sin(theta);
    pts.push([x, y]);
  }
  return pts
    .map((p, i) => `${i === 0 ? "M" : "L"} ${fmt(p[0])} ${fmt(p[1])}`)
    .join(" ");
}

/** Stilisierte Helix-Schraube: gestapelte Ellipsen-Boegen, absteigend. */
function helixPfad(): string {
  const rx = SPAN / 2 - 1;
  const ry = 5;
  const yTop = A + 3;
  const yBot = B - 3;
  const umdrehungen = 3;
  const dy = (yBot - yTop) / umdrehungen;
  const parts: string[] = [`M ${fmt(MID - rx)} ${fmt(yTop)}`];
  for (let i = 0; i < umdrehungen; i++) {
    const y0 = yTop + i * dy;
    const yHalf = y0 + dy / 2;
    const yFull = y0 + dy;
    // vordere (sichtbare) Haelfte: links -> rechts, nach unten gewoelbt
    parts.push(`A ${fmt(rx)} ${fmt(ry)} 0 0 0 ${fmt(MID + rx)} ${fmt(yHalf)}`);
    // hintere Haelfte: rechts -> links, weiter absteigend
    parts.push(`A ${fmt(rx)} ${fmt(ry)} 0 0 0 ${fmt(MID - rx)} ${fmt(yFull)}`);
  }
  return parts.join(" ");
}

// ---------------------------------------------------------------------------
// Marker (Pfeilspitzen) — kontextfarben
// ---------------------------------------------------------------------------

function Marker({ id }: { id: string }) {
  return (
    <marker
      id={id}
      markerWidth={6}
      markerHeight={6}
      refX={4.5}
      refY={3}
      orient="auto"
      markerUnits="userSpaceOnUse"
    >
      <path d="M0,0 L6,3 L0,6 Z" fill="currentColor" />
    </marker>
  );
}

// ---------------------------------------------------------------------------
// Einzel-Piktogramme
// ---------------------------------------------------------------------------

/** Abgerundeter Material-/Taschen-Rahmen als gemeinsamer Hintergrund. */
function TaschenRahmen() {
  return (
    <rect
      x={A - 2}
      y={A - 2}
      width={SPAN + 4}
      height={SPAN + 4}
      rx={6}
      fill="currentColor"
      fillOpacity={FILL_OP}
      stroke="currentColor"
      strokeOpacity={GHOST_OP}
      strokeWidth={1.5}
    />
  );
}

function PiktoParallel({ arrId }: { arrId: string }) {
  return (
    <>
      <TaschenRahmen />
      <path
        d={zickzackPfad(5)}
        fill="none"
        stroke="currentColor"
        strokeOpacity={PATH_OP}
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
        markerEnd={`url(#${arrId})`}
      />
    </>
  );
}

function PiktoSpirale({
  richtung,
  arrId,
}: {
  richtung: "ein" | "aus";
  arrId: string;
}) {
  const { d } = spiralePfad(richtung);
  return (
    <>
      <TaschenRahmen />
      <path
        d={d}
        fill="none"
        stroke="currentColor"
        strokeOpacity={PATH_OP}
        strokeWidth={2}
        strokeLinecap="round"
        markerEnd={`url(#${arrId})`}
      />
      <circle cx={MID} cy={MID} r={1.4} fill="currentColor" />
    </>
  );
}

function PiktoOffsetKontur() {
  return (
    <>
      <TaschenRahmen />
      {offsetKonturen().map((k, i) => (
        <rect
          key={i}
          x={k.x}
          y={k.y}
          width={k.w}
          height={k.h}
          rx={k.r}
          fill="none"
          stroke="currentColor"
          strokeOpacity={PATH_OP}
          strokeWidth={i === 0 ? 2 : 1.6}
        />
      ))}
    </>
  );
}

function PiktoAdaptive({ arrId }: { arrId: string }) {
  return (
    <>
      <TaschenRahmen />
      <path
        d={trochoidPfad()}
        fill="none"
        stroke="currentColor"
        strokeOpacity={PATH_OP}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        markerEnd={`url(#${arrId})`}
      />
    </>
  );
}

/** Material-Block (Querschnitt) mit Oberkante — Basis fuer Eintauch-Bilder. */
function MaterialBlock() {
  const top = A + 6;
  return (
    <>
      <rect
        x={A - 2}
        y={top}
        width={SPAN + 4}
        height={B - top}
        rx={2}
        fill="currentColor"
        fillOpacity={FILL_OP}
        stroke="currentColor"
        strokeOpacity={GHOST_OP}
        strokeWidth={1.5}
      />
      {/* Oberflaechen-Schraffur als Material-Andeutung */}
      <line
        x1={A - 2}
        y1={top}
        x2={B + 2}
        y2={top}
        stroke="currentColor"
        strokeOpacity={GHOST_OP}
        strokeWidth={1.5}
      />
    </>
  );
}

function PiktoSenkrecht({ arrId }: { arrId: string }) {
  const top = A + 1;
  const bot = B - 3;
  return (
    <>
      <MaterialBlock />
      <line
        x1={MID}
        y1={top}
        x2={MID}
        y2={bot}
        stroke="currentColor"
        strokeOpacity={PATH_OP}
        strokeWidth={2.4}
        strokeLinecap="round"
        markerEnd={`url(#${arrId})`}
      />
    </>
  );
}

function PiktoRampe({ arrId }: { arrId: string }) {
  const yTop = A + 6;
  const bot = B - 3;
  // diagonale Rampe hinein, dann kurzes Stueck auf Tiefe
  const d = `M ${fmt(A)} ${fmt(yTop)} L ${fmt(B - 4)} ${fmt(bot)} L ${fmt(A + 6)} ${fmt(bot)}`;
  return (
    <>
      <MaterialBlock />
      <path
        d={d}
        fill="none"
        stroke="currentColor"
        strokeOpacity={PATH_OP}
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
        markerEnd={`url(#${arrId})`}
      />
    </>
  );
}

function PiktoHelix({ arrId }: { arrId: string }) {
  return (
    <>
      <MaterialBlock />
      <path
        d={helixPfad()}
        fill="none"
        stroke="currentColor"
        strokeOpacity={PATH_OP}
        strokeWidth={2.2}
        strokeLinecap="round"
        markerEnd={`url(#${arrId})`}
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Beschriftung + Auswahl
// ---------------------------------------------------------------------------

const LABELS: Record<string, string> = {
  parallel: "Parallel (Zickzack)",
  spiral_aussen: "Spirale von aussen",
  spiral_innen: "Spirale von innen",
  offset_kontur: "Kontur-parallel (Offset)",
  adaptive: "Adaptiv (trochoidal)",
  senkrecht: "Senkrecht eintauchen",
  rampe: "Rampe",
  helix: "Helix",
};

function label(art: StrategieArt, wert: string): string {
  return LABELS[wert] ?? wert;
}

function renderPikto(
  art: StrategieArt,
  wert: string,
  arrId: string,
): JSX.Element {
  if (art === "tasche") {
    switch (wert) {
      case "parallel":
        return <PiktoParallel arrId={arrId} />;
      case "spiral_aussen":
        return <PiktoSpirale richtung="ein" arrId={arrId} />;
      case "spiral_innen":
        return <PiktoSpirale richtung="aus" arrId={arrId} />;
      case "offset_kontur":
        return <PiktoOffsetKontur />;
      case "adaptive":
        return <PiktoAdaptive arrId={arrId} />;
      default:
        return <TaschenRahmen />;
    }
  }
  // art === "eintauchen"
  switch (wert) {
    case "senkrecht":
      return <PiktoSenkrecht arrId={arrId} />;
    case "rampe":
      return <PiktoRampe arrId={arrId} />;
    case "helix":
      return <PiktoHelix arrId={arrId} />;
    default:
      return <MaterialBlock />;
  }
}

// ---------------------------------------------------------------------------
// Hauptkomponente
// ---------------------------------------------------------------------------

let _uid = 0;

export default function StrategieGrafik({
  art,
  wert,
  mode = "piktogramm",
  className,
  size,
  title,
}: Props) {
  const px = size ?? (mode === "gross" ? 96 : 28);
  // eindeutige Marker-ID, damit mehrere Instanzen sich nicht stoeren
  const arrId = `strat-arr-${art}-${String(wert)}-${(_uid = (_uid + 1) % 1e9)}`;
  const aria = title ?? `Strategie: ${label(art, String(wert))}`;

  return (
    <svg
      viewBox={`0 0 ${VB} ${VB}`}
      width={px}
      height={px}
      className={className}
      role="img"
      aria-label={aria}
    >
      <title>{aria}</title>
      <defs>
        <Marker id={arrId} />
      </defs>
      {renderPikto(art, String(wert), arrId)}
    </svg>
  );
}
