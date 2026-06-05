// Operation-Grafik: typ-abhaengiges, erklaerendes Piktogramm je Operations-Typ.
//
// Schwester-Komponente zu WerkzeugGrafik.tsx — gleiches Muster:
//   - parametrische SVG (festes Koordinatensystem, viewBox-skaliert)
//   - reine SVG, keine externen Libs
//   - Farbe ueber currentColor (erbt die Textfarbe des Kontexts),
//     Akzent-Highlights ueber das CSS-Token --camwosa-accent
//   - mode="piktogramm": kleine Skizze ohne Text (Buttons/Listen/Dropdowns)
//   - mode="gross":      grosse Skizze mit erklaerender Beschriftung
//
// Anders als WerkzeugGrafik (zeigt die *Geometrie eines Fraesers*) zeigt diese
// Komponente, *was die Operation mit dem Material macht*:
//   kontur  — Werkzeug faehrt an einer Linie entlang (aussen/innen) = durchschneiden
//   tasche  — eine Flaeche wird flaechig ausgeraeumt / ausgehoehlt
//   bohren  — ein Loch wird gesetzt (Spirale + Spaene)
//   gravur  — V-Spitze ritzt eine schmale Linie ins Material
//   relief  — 3D-Hoehenprofil wird zeilenweise abgefahren
//
// Die Skizzen sind stilisiert (gut erkennbar), nicht massstabsgetreu.

import type { OperationsTyp } from "../api/types";

// Diese Komponente deckt die fuenf "klassischen" Operationen ab. Die uebrigen
// OperationsTyp-Werte (drechseln/eilgang) haben eigene Darstellungen und werden
// hier bewusst nicht gezeichnet.
export type OperationGrafikTyp =
  | "kontur" | "tasche" | "bohren" | "gravur" | "relief";

interface Props {
  typ: OperationsTyp;
  mode?: "piktogramm" | "gross";
  className?: string;
  size?: number; // Pixel-Kante (Breite) der Grafik
}

// Gemeinsames Koordinatensystem (quadratisch, damit die Piktogramme zu den
// Werkzeug-Skizzen passen, aber operationstypisch breiter genutzt).
const W = 96;
const H = 96;

const LABELS: Record<OperationGrafikTyp, string> = {
  kontur: "Kontur — entlang der Linie schneiden",
  tasche: "Tasche — Flaeche ausraeumen",
  bohren: "Bohren — Loch setzen",
  gravur: "Gravur — Linie ritzen",
  relief: "Relief — 3D-Hoehenprofil",
};

const ACCENT = "var(--camwosa-accent, #38bdf8)";

/** Hilfsfarben: Werkstueck-Fuellung dezent, Schnitt/Werkzeug betont. */
const MAT_FILL = 0.1; // Material-Flaeche
const MAT_STROKE = 0.5; // Material-Kante

/** Werkstueck-Block als dezenter Hintergrund (gemeinsam fuer mehrere Typen). */
function block(x: number, y: number, w: number, h: number, rx = 3): JSX.Element {
  return (
    <rect
      x={x}
      y={y}
      width={w}
      height={h}
      rx={rx}
      fill="currentColor"
      fillOpacity={MAT_FILL}
      stroke="currentColor"
      strokeOpacity={MAT_STROKE}
      strokeWidth={1.5}
    />
  );
}

/** kontur: Werkzeug-Kreis faehrt an einer geschlossenen Kontur entlang. */
function kontur(): JSX.Element {
  // Werkstueck-Kontur (geschlossener Pfad) + Werkzeug (Kreis) auf der Bahn,
  // Pfeil zeigt Fahrtrichtung; gestrichelte Bahn = Fraeser-Mittelpunkt.
  const path = "M 22 26 L 62 26 Q 74 26 74 38 L 74 64 Q 74 74 64 74 L 30 74 Q 22 74 22 64 Z";
  return (
    <g fill="none">
      {/* Material-Flaeche */}
      <path d={path} fill="currentColor" fillOpacity={MAT_FILL} stroke="currentColor" strokeOpacity={MAT_STROKE} strokeWidth={1.5} />
      {/* Fraeser-Bahn (Offset entlang der Kontur) */}
      <path d={path} stroke={ACCENT} strokeWidth={1.4} strokeDasharray="3 3" opacity={0.85} />
      {/* Werkzeug (Schneide) auf der Bahn */}
      <circle cx={74} cy={38} r={6.5} fill={ACCENT} fillOpacity={0.25} stroke={ACCENT} strokeWidth={1.6} />
      {/* Fahrtrichtungs-Pfeil */}
      <path d="M 74 30 L 80 38 L 74 36 L 68 38 Z" fill={ACCENT} />
    </g>
  );
}

/** tasche: eine Flaeche wird durch parallele/spiralige Bahnen ausgeraeumt. */
function tasche(): JSX.Element {
  // Aeusserer Rahmen = Taschen-Grenze; innen eingesetzte Offset-Schleifen
  // (Ausraeum-Bahnen). Kleiner Fraeser-Kreis in einer Ecke deutet Eingriff an.
  return (
    <g fill="none">
      {block(20, 22, 56, 52, 4)}
      {/* Offset-Ausraeumbahnen nach innen */}
      <rect x={27} y={29} width={42} height={38} rx={3} stroke={ACCENT} strokeWidth={1.3} opacity={0.5} />
      <rect x={34} y={36} width={28} height={24} rx={2} stroke={ACCENT} strokeWidth={1.3} opacity={0.65} />
      <rect x={41} y={43} width={14} height={10} rx={1.5} stroke={ACCENT} strokeWidth={1.3} opacity={0.8} />
      {/* Werkzeug im Eingriff */}
      <circle cx={48} cy={48} r={5} fill={ACCENT} fillOpacity={0.3} stroke={ACCENT} strokeWidth={1.6} />
    </g>
  );
}

/** bohren: ein Loch wird mit der Bohrerspitze gesetzt (Spirale + Spaene). */
function bohren(): JSX.Element {
  // Material-Block mit Loch (dunkler Kreis), Bohrer-Spirale darin,
  // angedeutete Spaene am Rand.
  return (
    <g fill="none">
      {block(20, 24, 56, 48, 4)}
      {/* Loch */}
      <circle cx={48} cy={48} r={11} fill="currentColor" fillOpacity={0.18} stroke="currentColor" strokeOpacity={MAT_STROKE} strokeWidth={1.4} />
      {/* Bohrer-Spirale (zwei gegenlaeufige Boegen) */}
      <path d="M 41 41 A 9 9 0 0 1 55 55" stroke={ACCENT} strokeWidth={1.6} />
      <path d="M 43 53 A 7 7 0 0 1 53 43" stroke={ACCENT} strokeWidth={1.6} opacity={0.7} />
      {/* Bohrerspitze in der Mitte */}
      <circle cx={48} cy={48} r={2} fill={ACCENT} />
    </g>
  );
}

/** gravur: V-Spitze ritzt eine schmale Linie ins Material (Querschnitt). */
function gravur(): JSX.Element {
  // Querschnitt: Material-Oberkante als Linie, V-foermige Nut nach unten,
  // darueber das V-Bit (auf den Kopf gestellt) das gerade ritzt.
  const top = 54; // Hoehe der Material-Oberflaeche
  return (
    <g fill="none">
      {/* Material (Block bis Oberkante) */}
      {block(16, top, 64, 26, 2)}
      {/* V-Nut in der Oberflaeche */}
      <path d={`M 16 ${top} L 80 ${top}`} stroke="currentColor" strokeOpacity={MAT_STROKE} strokeWidth={1.5} />
      <path d={`M 42 ${top} L 48 ${top + 12} L 54 ${top}`} fill="currentColor" fillOpacity={0.18} stroke="currentColor" strokeOpacity={MAT_STROKE} strokeWidth={1.2} />
      {/* V-Bit (Schaft + konische Spitze, ritzt von oben) */}
      <path d="M 44 16 L 52 16 L 52 30 L 48 40 L 44 30 Z" fill={ACCENT} fillOpacity={0.25} stroke={ACCENT} strokeWidth={1.6} strokeLinejoin="round" />
      {/* Eintauch-Pfeil */}
      <path d="M 48 42 L 48 50 M 45 47 L 48 51 L 51 47" stroke={ACCENT} strokeWidth={1.4} />
    </g>
  );
}

/** relief: 3D-Hoehenprofil, zeilenweise vom Kugelfraeser abgefahren. */
function relief(): JSX.Element {
  // Gewelltes Hoehenprofil (Schnittkante) + parallele Abtast-Zeilen darunter,
  // Kugelfraeser folgt der obersten Welle.
  const wave = "M 16 50 C 28 30 40 64 52 44 C 62 28 72 56 80 40";
  return (
    <g fill="none">
      {/* Material-Block unter dem Profil */}
      <path d={`${wave} L 80 78 L 16 78 Z`} fill="currentColor" fillOpacity={MAT_FILL} stroke="none" />
      {/* gefraeste Hoehen-Kontur (oberste Zeile) */}
      <path d={wave} stroke={ACCENT} strokeWidth={2} opacity={0.9} />
      {/* tiefere Abtast-Zeilen (gedaempfte Wiederholungen) */}
      <path d="M 16 60 C 28 44 40 70 52 54 C 62 42 72 64 80 52" stroke={ACCENT} strokeWidth={1.2} opacity={0.45} />
      <path d="M 16 70 C 28 58 40 76 52 66 C 62 58 72 72 80 64" stroke={ACCENT} strokeWidth={1.2} opacity={0.3} />
      {/* Kugelfraeser auf der obersten Welle */}
      <circle cx={52} cy={44} r={5.5} fill={ACCENT} fillOpacity={0.25} stroke={ACCENT} strokeWidth={1.6} />
    </g>
  );
}

const ZEICHNER: Record<OperationGrafikTyp, () => JSX.Element> = {
  kontur,
  tasche,
  bohren,
  gravur,
  relief,
};

/** True, wenn fuer diesen Typ eine Skizze existiert. */
export function hatOperationGrafik(typ: OperationsTyp): typ is OperationGrafikTyp {
  return typ in ZEICHNER;
}

export default function OperationGrafik({
  typ, mode = "piktogramm", className, size,
}: Props) {
  const px = size ?? (mode === "gross" ? 150 : 28);
  const labelH = mode === "gross" ? 16 : 0; // Platz fuer die Beschriftung
  const vb = `0 0 ${W} ${H + labelH}`;
  const height = (px * (H + labelH)) / W;

  if (!hatOperationGrafik(typ)) {
    // Unbekannter/nicht abgedeckter Typ: leeres, aber valides SVG.
    return (
      <svg
        viewBox={vb}
        width={px}
        height={height}
        className={className}
        role="img"
        aria-label={`Operation ${typ}`}
      />
    );
  }

  const label = LABELS[typ];

  return (
    <svg
      viewBox={vb}
      width={px}
      height={height}
      className={className}
      role="img"
      aria-label={`Operations-Skizze ${label}`}
    >
      {ZEICHNER[typ]()}
      {mode === "gross" && (
        <text
          x={W / 2}
          y={H + 11}
          fill="currentColor"
          opacity={0.7}
          fontSize={8}
          fontFamily="ui-monospace, monospace"
          textAnchor="middle"
        >
          {label}
        </text>
      )}
    </svg>
  );
}
