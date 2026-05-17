/**
 * Pattern-Transformationen fuer Wrap-Designs.
 *
 * Funktionen sind pure (nehmen Punkt-Liste, geben neue Punkt-Liste zurueck) —
 * damit gut unit-testbar und ohne Side-Effects.
 */

export type WrapPunkt = [number, number];

export interface BoundingBox {
  min_x: number;
  min_y: number;
  max_x: number;
  max_y: number;
  breite_x: number;
  hoehe_y: number;
}

export function bbox(punkte: WrapPunkt[]): BoundingBox | null {
  if (!punkte.length) return null;
  let min_x = Infinity, min_y = Infinity, max_x = -Infinity, max_y = -Infinity;
  for (const [x, y] of punkte) {
    if (x < min_x) min_x = x;
    if (y < min_y) min_y = y;
    if (x > max_x) max_x = x;
    if (y > max_y) max_y = y;
  }
  return {
    min_x, min_y, max_x, max_y,
    breite_x: max_x - min_x,
    hoehe_y: max_y - min_y,
  };
}

/**
 * Verschiebt alle Punkte so dass die BoundingBox bei (0, 0) startet.
 * Nuetzlich vor dem Skalieren oder Wickeln (Pattern soll am Werkstueck-Anfang sitzen).
 */
export function normalisieren(punkte: WrapPunkt[]): WrapPunkt[] {
  const b = bbox(punkte);
  if (!b) return [];
  return punkte.map(([x, y]) => [x - b.min_x, y - b.min_y]);
}

/**
 * Skaliert alle Punkte um den BoundingBox-Mittelpunkt mit getrennten
 * Faktoren fuer X und Y. Snap auf 0.5 mm fuers gute Gefuehl.
 */
export function skaliere(
  punkte: WrapPunkt[],
  scale_x: number,
  scale_y: number = scale_x,
): WrapPunkt[] {
  if (!punkte.length) return [];
  const b = bbox(punkte)!;
  const cx = (b.min_x + b.max_x) / 2;
  const cy = (b.min_y + b.max_y) / 2;
  return punkte.map(([x, y]) => [
    Math.round((cx + (x - cx) * scale_x) * 2) / 2,
    Math.round((cy + (y - cy) * scale_y) * 2) / 2,
  ]);
}

/**
 * Skaliert das Pattern so dass es eine Soll-Breite (X) und/oder Soll-Hoehe (Y) hat.
 * Wenn nur ein Wert gesetzt ist, wird der andere proportional mitskaliert
 * (= proportional skalieren).
 */
export function skaliere_auf(
  punkte: WrapPunkt[],
  ziel_breite_x_mm: number | null,
  ziel_hoehe_y_mm: number | null,
): WrapPunkt[] {
  const b = bbox(punkte);
  if (!b || (b.breite_x === 0 && b.hoehe_y === 0)) return punkte;

  let fx = 1, fy = 1;
  if (ziel_breite_x_mm != null && b.breite_x > 0) {
    fx = ziel_breite_x_mm / b.breite_x;
  }
  if (ziel_hoehe_y_mm != null && b.hoehe_y > 0) {
    fy = ziel_hoehe_y_mm / b.hoehe_y;
  }
  // Wenn nur eines gesetzt: proportional
  if (ziel_breite_x_mm == null) fx = fy;
  if (ziel_hoehe_y_mm == null) fy = fx;

  return skaliere(punkte, fx, fy);
}

/**
 * Skaliert das Pattern so dass es **exakt einmal rundum** den Werkstueck-Umfang
 * passt — typische Use-Case fuer Muster die rundherum gehen sollen.
 * X bleibt proportional mitskaliert (sonst wuerde Schrift gestaucht).
 */
export function skaliere_auf_umfang(
  punkte: WrapPunkt[],
  werkstueck_radius_mm: number,
): WrapPunkt[] {
  const umfang = 2 * Math.PI * werkstueck_radius_mm;
  return skaliere_auf(punkte, null, umfang);
}

/**
 * Skaliert proportional und passt das Pattern in den Werkstueck-Umfang
 * (= max Y-Spanne <= Umfang) UND in eine maximale X-Laenge ein —
 * typisch fuer „so gross wie moeglich aber passt rein".
 */
export function skaliere_auf_passend(
  punkte: WrapPunkt[],
  werkstueck_radius_mm: number,
  max_x_mm: number,
): WrapPunkt[] {
  const b = bbox(punkte);
  if (!b) return punkte;
  const umfang = 2 * Math.PI * werkstueck_radius_mm;
  const fx_max = b.breite_x > 0 ? max_x_mm / b.breite_x : Infinity;
  const fy_max = b.hoehe_y > 0 ? umfang / b.hoehe_y : Infinity;
  const f = Math.min(fx_max, fy_max);
  if (!isFinite(f) || f <= 0) return punkte;
  return skaliere(punkte, f, f);
}

/**
 * Verschiebt alle Punkte um Delta (z.B. um das Pattern auf eine Position
 * am Werkstueck zu setzen).
 */
export function verschieben(
  punkte: WrapPunkt[], dx: number, dy: number,
): WrapPunkt[] {
  return punkte.map(([x, y]) => [
    Math.round((x + dx) * 2) / 2,
    Math.round((y + dy) * 2) / 2,
  ]);
}

/**
 * Rotiert alle Punkte um den BoundingBox-Mittelpunkt (Grad).
 * Achtung: nur die XY-Koordinaten — Y-Werte werden danach trotzdem als
 * Bogenlaenge interpretiert (also nicht „Rotation am Werkstueck", sondern
 * „Rotation des abgewickelten Designs vor dem Wickeln").
 */
export function rotieren_design(
  punkte: WrapPunkt[], grad: number,
): WrapPunkt[] {
  if (!punkte.length) return [];
  const b = bbox(punkte)!;
  const cx = (b.min_x + b.max_x) / 2;
  const cy = (b.min_y + b.max_y) / 2;
  const rad = grad * Math.PI / 180;
  const cosA = Math.cos(rad);
  const sinA = Math.sin(rad);
  return punkte.map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    return [
      Math.round((cx + dx * cosA - dy * sinA) * 2) / 2,
      Math.round((cy + dx * sinA + dy * cosA) * 2) / 2,
    ];
  });
}
