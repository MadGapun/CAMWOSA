// Kontur-Seite + Haltestege-Grafik: erklaerende SVG-Skizze fuer die
// Kontur-Operation (Issue #33 Folge, Stil-Muster aus WerkzeugGrafik.tsx).
//
// Markus' Anforderung: das Feld „Seite" (innen / aussen / auf_linie) ist fuer
// Einsteiger nicht selbsterklaerend — eine Grafik soll zeigen, auf welcher
// SEITE der Zeichnungslinie das Werkzeug laeuft und welches Material uebrig
// bleibt. Ebenso sollen die Haltestege (Tabs) erklaert werden: ohne Tabs
// faellt das ausgeschnittene Teil heraus und kann verlaufen / vom Fraeser
// erfasst werden.
//
// Die Komponente ist rein praesentativ (nur SVG, kein State). Sie nimmt die
// aktuelle Auswahl entgegen und hebt die zugehoerige Variante hervor — so
// dient sie als Live-Legende direkt neben dem „Seite"- bzw. „Tabs"-Feld.
//
// Darstellung (nicht massstabsgetreu, aber semantisch korrekt):
//   - Zeichnungslinie  = gestrichelt, neutral (das ist die CAD-Geometrie)
//   - Werkzeug-Bahn    = Mittelpunktbahn des Fraesers, akzentfarben
//   - Werkzeug         = Kreis (Fraeser-Durchmesser) auf der Bahn
//   - „Teil" (bleibt)  = gefuellte Flaeche, die nach dem Schnitt uebrig ist
//   - Schnittfuge      = der vom Fraeser geraeumte Bereich
//
// Farben kommen aus den CSS-Tokens (tokens.css): --accent (orange),
// --warning, --danger, --success, --text-muted. Fallbacks sind gesetzt, damit
// die Grafik auch ohne geladene Tokens (z.B. im SSR-Test) korrekt rendert.

import type { OperationsTyp } from "../api/types";

/** Welche Kontur-Seite ist aktuell gewaehlt? (= Werte des „Seite"-Felds). */
export type KonturSeite = "innen" | "aussen" | "auf_linie";

interface Props {
  /** Aktuell gewaehlte Seite — die zugehoerige Variante wird hervorgehoben.
   *  null/undefined = keine Hervorhebung (alle Varianten neutral). */
  seite?: KonturSeite | null;
  /** Aktuelle Tab-Anzahl (aus dem „Tabs Anzahl"-Feld). Steuert die
   *  Haltestege-Skizze: 0 = „Teil faellt heraus"-Warnung. */
  tabsAnzahl?: number | null;
  /** Welcher Block soll gezeigt werden? Default: beide untereinander.
   *  - "seite"  nur die Innen/Aussen/Auf-Linie-Erklaerung
   *  - "tabs"   nur die Haltestege-Erklaerung
   *  - "beide"  beides (Default) */
  zeige?: "seite" | "tabs" | "beide";
  className?: string;
  /** Operations-Typ — die Grafik ist nur fuer „kontur" sinnvoll. Bei anderen
   *  Typen rendert die Komponente nichts (bequem als Guard im Formular). */
  typ?: OperationsTyp;
}

// ---- Farben (CSS-Tokens mit Fallback) ----------------------------------
const C_ACCENT = "var(--accent, #FF6B00)";
const C_WARN = "var(--warning, #FFB800)";
const C_DANGER = "var(--danger, #FF453A)";
const C_OK = "var(--success, #00C26E)";
const C_MUTED = "var(--text-muted, #6B6B73)";
const C_LINE = "currentColor";

// ---- Geometrie der Mini-Skizzen ----------------------------------------
// Jede Seiten-Variante ist ein quadratisches Panel. Wir zeichnen ein
// abgerundetes Rechteck als „Zeichnungslinie" und legen das Werkzeug an einer
// Ecke an, damit Versatz nach innen/aussen/auf-Linie deutlich sichtbar ist.
const PANEL = 96; // ViewBox-Kante eines Seiten-Panels
const RX = 22; // halbe Werkzeug-Breite (Radius), bewusst gross fuer Klarheit

/** Geometrie des „Zeichnungs"-Rechtecks innerhalb eines Panels. */
const RECT = { x: 24, y: 24, w: 48, h: 48, r: 7 };

/**
 * Rechteck-Pfad (abgerundet), optional nach aussen/innen versetzt.
 * offset > 0 => groesser (Bahn aussen), offset < 0 => kleiner (Bahn innen).
 */
function rectPath(offset: number): string {
  const x = RECT.x - offset;
  const y = RECT.y - offset;
  const w = RECT.w + offset * 2;
  const h = RECT.h + offset * 2;
  const r = Math.max(0, RECT.r + offset);
  return (
    `M ${x + r} ${y}` +
    ` H ${x + w - r}` +
    ` A ${r} ${r} 0 0 1 ${x + w} ${y + r}` +
    ` V ${y + h - r}` +
    ` A ${r} ${r} 0 0 1 ${x + w - r} ${y + h}` +
    ` H ${x + r}` +
    ` A ${r} ${r} 0 0 1 ${x} ${y + h - r}` +
    ` V ${y + r}` +
    ` A ${r} ${r} 0 0 1 ${x + r} ${y} Z`
  );
}

/** Halber Werkzeug-Versatz fuer ein Panel (Bahn liegt um RX/2 versetzt). */
const OFF = RX / 2;

interface SeitenDef {
  key: KonturSeite;
  titel: string;
  /** kurze Erklaerung unter dem Panel */
  hinweis: string;
  /** Versatz der Werkzeug-Bahn relativ zur Linie (px) */
  bahnOffset: number;
  /** Position des Werkzeug-Kreises (Mittelpunkt liegt auf der Bahn) */
  toolCenter: { cx: number; cy: number };
}

// Werkzeug sitzt jeweils oben-rechts an der Linie, damit der Versatz auffaellt.
const ECKE = { x: RECT.x + RECT.w, y: RECT.y };

const SEITEN: SeitenDef[] = [
  {
    key: "aussen",
    titel: "Aussen",
    hinweis: "Fraeser laeuft AUSSERHALB — das Teil bleibt voll erhalten (Aussenkontur).",
    bahnOffset: OFF,
    toolCenter: { cx: ECKE.x + OFF, cy: ECKE.y - OFF },
  },
  {
    key: "auf_linie",
    titel: "Auf Linie",
    hinweis: "Mitte des Fraesers liegt AUF der Linie — fuer Gravur/Nut, kein Versatz.",
    bahnOffset: 0,
    toolCenter: { cx: ECKE.x, cy: ECKE.y },
  },
  {
    key: "innen",
    titel: "Innen",
    hinweis: "Fraeser laeuft INNERHALB — fuer Taschen/Durchbrueche, Mass wird kleiner.",
    bahnOffset: -OFF,
    toolCenter: { cx: ECKE.x - OFF, cy: ECKE.y + OFF },
  },
];

/** Ein einzelnes Seiten-Panel (innen / aussen / auf_linie). */
function SeitenPanel({
  def,
  aktiv,
}: {
  def: SeitenDef;
  aktiv: boolean;
}) {
  const bahn = C_ACCENT;
  return (
    <figure className="m-0 flex flex-col items-center">
      <svg
        viewBox={`0 0 ${PANEL} ${PANEL}`}
        width="100%"
        className="block"
        role="img"
        aria-label={`Kontur-Seite ${def.titel}`}
        style={{ color: C_MUTED }}
      >
        {/* Rahmen / Hervorhebung der aktiven Variante */}
        <rect
          x={1.5}
          y={1.5}
          width={PANEL - 3}
          height={PANEL - 3}
          rx={8}
          fill={aktiv ? "var(--accent-soft, rgba(255,107,0,0.12))" : "transparent"}
          stroke={aktiv ? C_ACCENT : "var(--border-subtle, #2A2A30)"}
          strokeWidth={aktiv ? 1.6 : 1}
        />

        {/* „Teil bleibt"-Flaeche: bei aussen das Innere, bei innen das Aeussere */}
        {def.key === "aussen" && (
          <path d={rectPath(0)} fill={C_OK} fillOpacity={0.12} stroke="none" />
        )}
        {def.key === "innen" && (
          // Material aussen bleibt: ganzes Panel minus Loch (evenodd)
          <path
            d={`M0 0 H${PANEL} V${PANEL} H0 Z ${rectPath(0)}`}
            fill={C_OK}
            fillOpacity={0.1}
            fillRule="evenodd"
            stroke="none"
          />
        )}

        {/* Werkzeug-Bahn (Mittelpunktbahn) */}
        <path
          d={rectPath(def.bahnOffset)}
          fill="none"
          stroke={bahn}
          strokeWidth={1.6}
          strokeLinejoin="round"
        />

        {/* Zeichnungslinie (CAD-Geometrie) — gestrichelt, neutral, oben drauf */}
        <path
          d={rectPath(0)}
          fill="none"
          stroke={C_LINE}
          strokeWidth={1.4}
          strokeDasharray="3 2.5"
          strokeLinejoin="round"
          opacity={0.85}
        />

        {/* Werkzeug-Kreis an der Ecke (zeigt Durchmesser + Versatz) */}
        <g>
          <circle
            cx={def.toolCenter.cx}
            cy={def.toolCenter.cy}
            r={RX}
            fill={bahn}
            fillOpacity={0.14}
            stroke={bahn}
            strokeWidth={1.4}
          />
          {/* Werkzeug-Mittelpunkt */}
          <circle cx={def.toolCenter.cx} cy={def.toolCenter.cy} r={1.6} fill={bahn} />
          {/* Versatz-Pfeil von Linie zur Bahn (nur wenn es einen Versatz gibt) */}
          {def.bahnOffset !== 0 && (
            <line
              x1={ECKE.x}
              y1={ECKE.y}
              x2={def.toolCenter.cx}
              y2={def.toolCenter.cy}
              stroke={bahn}
              strokeWidth={1.2}
              markerEnd="url(#ks-arr)"
            />
          )}
        </g>
      </svg>
      <figcaption className="mt-1 text-center">
        <span
          className="text-[11px] font-semibold"
          style={{ color: aktiv ? C_ACCENT : "var(--text-secondary, #A0A0A8)" }}
        >
          {def.titel}
        </span>
        <span className="mt-0.5 block text-[10px] leading-snug text-camwosa-muted">
          {def.hinweis}
        </span>
      </figcaption>
    </figure>
  );
}

// ---- Haltestege (Tabs) -------------------------------------------------
// Querschnitt-Ansicht: das ausgeschnittene Teil im umgebenden Rohmaterial.
// Mit Tabs bleiben kleine Materialbruecken am Boden stehen, die das Teil
// halten. Ohne Tabs faellt das losgeschnittene Teil heraus.
const TABS_W = 320;
const TABS_H = 132;

/** Skizze: Werkstueck im Schnitt mit N Haltestegen (oder Warnung bei 0). */
function TabsPanel({ tabsAnzahl }: { tabsAnzahl: number }) {
  const n = Math.max(0, Math.floor(tabsAnzahl));
  const ohneTabs = n === 0;

  // Layout des Werkstuecks (Querschnitt von der Seite gesehen)
  const matTop = 30;
  const matBot = 96;
  const matLeft = 16;
  const matRight = TABS_W - 16;
  const partLeft = 96;
  const partRight = TABS_W - 96;
  const gap = 16; // Breite der Schnittfuge links/rechts vom Teil
  const tabBreite = 16;
  const tabHoehe = 12; // wie hoch der Steg vom Boden hoch steht

  // Positionen der Stege gleichmaessig ueber die Teil-Breite verteilt
  const tabXs: number[] = [];
  if (n > 0) {
    const span = partRight - partLeft;
    for (let i = 0; i < n; i++) {
      const f = n === 1 ? 0.5 : i / (n - 1);
      // Raender etwas einruecken, damit Stege nicht genau auf der Kante sitzen
      tabXs.push(partLeft + 8 + f * (span - 16));
    }
  }

  // Y-Versatz fuer „herausgefallenes" Teil (nur Illustration ohne Tabs)
  const dropY = ohneTabs ? 14 : 0;

  return (
    <svg
      viewBox={`0 0 ${TABS_W} ${TABS_H}`}
      width="100%"
      className="block"
      role="img"
      aria-label={ohneTabs ? "Kontur ohne Haltestege" : `Kontur mit ${n} Haltestegen`}
      style={{ color: C_MUTED }}
    >
      <defs>
        <pattern id="ks-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke={C_MUTED} strokeWidth="1" opacity="0.5" />
        </pattern>
      </defs>

      {/* Umgebendes Rohmaterial links */}
      <rect
        x={matLeft}
        y={matTop}
        width={partLeft - gap - matLeft}
        height={matBot - matTop}
        fill="url(#ks-hatch)"
        stroke={C_MUTED}
        strokeWidth={1.2}
      />
      {/* Umgebendes Rohmaterial rechts */}
      <rect
        x={partRight + gap}
        y={matTop}
        width={matRight - (partRight + gap)}
        height={matBot - matTop}
        fill="url(#ks-hatch)"
        stroke={C_MUTED}
        strokeWidth={1.2}
      />

      {/* Schnittfugen (vom Fraeser geraeumt) links + rechts */}
      <rect x={partLeft - gap} y={matTop} width={gap} height={matBot - matTop} fill={C_ACCENT} fillOpacity={0.1} />
      <rect x={partRight} y={matTop} width={gap} height={matBot - matTop} fill={C_ACCENT} fillOpacity={0.1} />

      {/* Das ausgeschnittene Teil */}
      <g transform={`translate(0 ${dropY})`}>
        <rect
          x={partLeft}
          y={matTop}
          width={partRight - partLeft}
          height={matBot - matTop}
          rx={2}
          fill={ohneTabs ? C_DANGER : C_OK}
          fillOpacity={0.16}
          stroke={ohneTabs ? C_DANGER : C_OK}
          strokeWidth={1.6}
        />
        <text
          x={(partLeft + partRight) / 2}
          y={(matTop + matBot) / 2 + 3}
          textAnchor="middle"
          fontSize={11}
          fontFamily="ui-monospace, monospace"
          fill={ohneTabs ? C_DANGER : C_OK}
          opacity={0.9}
        >
          Teil
        </text>
      </g>

      {/* Haltestege: kleine Bruecken am Boden, die Teil + Rohmaterial verbinden */}
      {!ohneTabs &&
        tabXs.map((x, i) => (
          <g key={i}>
            {/* Steg ueberbrueckt die Schnittfuge auf beiden Seiten gibt es einen;
                hier zeichnen wir den Steg ueber die jeweils naechste Fuge.
                Zur Vereinfachung: ein zentraler Steg-Block am Teil-Boden. */}
            <rect
              x={x - tabBreite / 2}
              y={matBot - tabHoehe}
              width={tabBreite}
              height={tabHoehe}
              rx={1.5}
              fill={C_WARN}
              fillOpacity={0.35}
              stroke={C_WARN}
              strokeWidth={1.3}
            />
          </g>
        ))}

      {/* Bodenlinie / Werkstueck-Unterkante als Bezug */}
      <line x1={matLeft} y1={matBot} x2={matRight} y2={matBot} stroke={C_MUTED} strokeWidth={1.4} opacity={0.7} />

      {/* Hinweis-Text */}
      {ohneTabs ? (
        <g>
          {/* Fall-Pfeil */}
          <line x1={(partLeft + partRight) / 2} y1={matBot - 8} x2={(partLeft + partRight) / 2} y2={matBot + 16}
            stroke={C_DANGER} strokeWidth={1.6} markerEnd="url(#ks-arr-d)" />
          <text x={TABS_W / 2} y={TABS_H - 6} textAnchor="middle" fontSize={11} fontWeight={600} fill={C_DANGER}>
            ⚠ Ohne Haltestege faellt das Teil heraus
          </text>
        </g>
      ) : (
        <text x={TABS_W / 2} y={TABS_H - 6} textAnchor="middle" fontSize={11} fill={C_WARN}>
          {n} {n === 1 ? "Haltesteg" : "Haltestege"} halten das Teil im Rohmaterial
        </text>
      )}

      <defs>
        <marker id="ks-arr-d" markerWidth={7} markerHeight={7} refX={3.5} refY={6} orient="auto">
          <path d="M0,0 L7,0 L3.5,7 Z" fill={C_DANGER} />
        </marker>
      </defs>
    </svg>
  );
}

/**
 * KonturSeiteGrafik — kombinierte Legende fuer das Kontur-Formular.
 *
 * Zeigt drei Mini-Skizzen (innen / auf_linie / aussen) mit Werkzeug-Versatz
 * und darunter eine Haltestege-Skizze. Die jeweils gewaehlte Variante wird
 * hervorgehoben, sodass die Grafik live zur Auswahl im Formular passt.
 */
export default function KonturSeiteGrafik({
  seite,
  tabsAnzahl,
  zeige = "beide",
  className,
  typ,
}: Props) {
  // Guard: nur fuer Kontur sinnvoll
  if (typ && typ !== "kontur") return null;

  const zeigeSeite = zeige === "beide" || zeige === "seite";
  const zeigeTabs = zeige === "beide" || zeige === "tabs";
  const effTabs = typeof tabsAnzahl === "number" ? tabsAnzahl : 3;

  return (
    <div
      className={
        "rounded border border-gray-700 bg-camwosa-bg/40 p-3 text-camwosa-muted " +
        (className ?? "")
      }
    >
      {/* gemeinsame Pfeil-Marker fuer die Seiten-Panels */}
      <svg width="0" height="0" className="absolute" aria-hidden>
        <defs>
          <marker id="ks-arr" markerWidth={6} markerHeight={6} refX={5} refY={3} orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill={C_ACCENT} />
          </marker>
        </defs>
      </svg>

      {zeigeSeite && (
        <div>
          <div className="mb-2 flex items-baseline justify-between">
            <h4 className="text-xs font-semibold text-camwosa-text">
              Werkzeug-Seite zur Linie
            </h4>
            <span className="text-[10px] text-camwosa-muted">
              <span className="mr-2">
                <span className="mr-1 inline-block h-2 w-3 border border-dashed align-middle" style={{ borderColor: C_LINE }} />
                Zeichnung
              </span>
              <span>
                <span className="mr-1 inline-block h-2 w-3 align-middle" style={{ backgroundColor: C_ACCENT, opacity: 0.6 }} />
                Werkzeug-Bahn
              </span>
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {SEITEN.map((def) => (
              <SeitenPanel key={def.key} def={def} aktiv={seite === def.key} />
            ))}
          </div>
        </div>
      )}

      {zeigeSeite && zeigeTabs && <hr className="my-3 border-gray-700" />}

      {zeigeTabs && (
        <div>
          <div className="mb-2 flex items-baseline justify-between">
            <h4 className="text-xs font-semibold text-camwosa-text">
              Haltestege (Tabs)
            </h4>
            <span className="text-[10px] text-camwosa-muted">Querschnitt durch das Werkstueck</span>
          </div>
          <TabsPanel tabsAnzahl={effTabs} />
        </div>
      )}
    </div>
  );
}
