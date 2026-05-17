import { useState } from "react";
import {
  bbox,
  normalisieren,
  rotieren_design,
  skaliere,
  skaliere_auf,
  skaliere_auf_passend,
  skaliere_auf_umfang,
  verschieben,
  type WrapPunkt,
} from "./wrapTransform";

interface Props {
  punkte: WrapPunkt[];
  onChange: (p: WrapPunkt[]) => void;
  werkstueck_radius_mm: number;
  werkstueck_laenge_mm: number;
}

/**
 * Transform-Panel fuer Wrap-Designs.
 *
 * Sektionen:
 * 1. **Skalieren**: Soll-Breite/Hoehe eingeben, „Rundum-passen"-Button, „Auto-Fit"
 * 2. **Verschieben**: dX/dY oder „Bei 0,0 starten" (Normalisieren)
 * 3. **Rotieren**: Design um seinen Mittelpunkt drehen
 * 4. **Anzeige**: aktuelle BoundingBox
 */
export default function WrapPatternTransform({
  punkte, onChange, werkstueck_radius_mm, werkstueck_laenge_mm,
}: Props) {
  const [zielBreite, setZielBreite] = useState<string>("");
  const [zielHoehe, setZielHoehe] = useState<string>("");
  const [scaleProz, setScaleProz] = useState(100);
  const [dx, setDx] = useState(0);
  const [dy, setDy] = useState(0);
  const [rotGrad, setRotGrad] = useState(0);

  const b = bbox(punkte);
  const umfang = 2 * Math.PI * werkstueck_radius_mm;

  if (!b) {
    return (
      <div className="rounded border border-camwosa-default bg-camwosa-surface p-3 text-xs text-camwosa-muted">
        Pattern leer — erst Punkte zeichnen, dann skalieren.
      </div>
    );
  }

  function anwenden_skalieren_auf() {
    const x = zielBreite ? Number(zielBreite) : null;
    const y = zielHoehe ? Number(zielHoehe) : null;
    onChange(skaliere_auf(punkte, x, y));
  }

  function anwenden_scale_prozent() {
    const f = scaleProz / 100;
    onChange(skaliere(punkte, f, f));
    setScaleProz(100);
  }

  function anwenden_verschieben() {
    onChange(verschieben(punkte, dx, dy));
    setDx(0); setDy(0);
  }

  function anwenden_rotieren() {
    onChange(rotieren_design(punkte, rotGrad));
    setRotGrad(0);
  }

  return (
    <div className="space-y-3 rounded border border-camwosa-default bg-camwosa-surface p-3 text-xs">
      <h3 className="text-sm font-semibold">Pattern-Transformationen</h3>

      {/* BBox-Anzeige */}
      <div className="grid grid-cols-2 gap-2 rounded bg-camwosa-bg p-2 font-mono text-[11px] sm:grid-cols-4">
        <div><span className="text-camwosa-muted">Breite X:</span> {b.breite_x.toFixed(1)} mm</div>
        <div><span className="text-camwosa-muted">Hoehe Y:</span> {b.hoehe_y.toFixed(1)} mm</div>
        <div><span className="text-camwosa-muted">Start X:</span> {b.min_x.toFixed(1)}</div>
        <div><span className="text-camwosa-muted">Start Y:</span> {b.min_y.toFixed(1)}</div>
      </div>

      {/* Skalieren auf Soll-Maße */}
      <section className="space-y-2">
        <div className="text-xs font-semibold text-camwosa-muted uppercase tracking-wider">
          Skalieren auf Soll-Maße
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label>
            <span className="block text-camwosa-muted">Soll-Breite X (mm)</span>
            <input
              type="number"
              value={zielBreite}
              onChange={(e) => setZielBreite(e.target.value)}
              placeholder="leer = proportional"
              className="w-32 rounded bg-camwosa-bg px-2 py-1"
            />
          </label>
          <label>
            <span className="block text-camwosa-muted">Soll-Hoehe Y (mm)</span>
            <input
              type="number"
              value={zielHoehe}
              onChange={(e) => setZielHoehe(e.target.value)}
              placeholder="leer = proportional"
              className="w-32 rounded bg-camwosa-bg px-2 py-1"
            />
          </label>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 font-medium text-camwosa-bg hover:opacity-90"
            onClick={anwenden_skalieren_auf}
            disabled={!zielBreite && !zielHoehe}
          >
            Skalieren
          </button>
          <span className="text-[10px] text-camwosa-muted">
            (nur ein Wert = proportional, beide = stauchen/strecken)
          </span>
        </div>
      </section>

      {/* Schnell-Buttons */}
      <section className="space-y-2">
        <div className="text-xs font-semibold text-camwosa-muted uppercase tracking-wider">
          Schnell-Aktionen
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
            onClick={() => onChange(skaliere_auf_umfang(punkte, werkstueck_radius_mm))}
            title={`Y-Spanne wird genau ${umfang.toFixed(1)}mm = 1× rund herum`}
          >
            ↻ Rundum-Passen (1 Umdrehung)
          </button>
          <button
            className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
            onClick={() => onChange(skaliere_auf_passend(punkte, werkstueck_radius_mm, werkstueck_laenge_mm * 0.9))}
            title="So gross wie moeglich, aber passt sowohl in Umfang als auch in Werkstueck-Laenge"
          >
            ⊞ Auto-Fit Werkstueck
          </button>
          <button
            className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
            onClick={() => onChange(normalisieren(punkte))}
            title="Pattern auf (0, 0) verschieben"
          >
            ↥ Bei 0, 0 starten
          </button>
        </div>
      </section>

      {/* Prozentual skalieren */}
      <section className="space-y-2">
        <div className="text-xs font-semibold text-camwosa-muted uppercase tracking-wider">
          Skalierung in Prozent
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="range"
            min={10} max={500} step={5}
            value={scaleProz}
            onChange={(e) => setScaleProz(Number(e.target.value))}
            className="flex-1"
          />
          <input
            type="number"
            value={scaleProz}
            onChange={(e) => setScaleProz(Number(e.target.value))}
            className="w-20 rounded bg-camwosa-bg px-2 py-1 text-right"
          />
          <span>%</span>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 font-medium text-camwosa-bg hover:opacity-90"
            onClick={anwenden_scale_prozent}
            disabled={scaleProz === 100}
          >
            Anwenden
          </button>
        </div>
      </section>

      {/* Verschieben */}
      <section className="space-y-2">
        <div className="text-xs font-semibold text-camwosa-muted uppercase tracking-wider">
          Verschieben
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label>
            <span className="block text-camwosa-muted">dX (mm)</span>
            <input
              type="number"
              value={dx}
              onChange={(e) => setDx(Number(e.target.value))}
              step={1}
              className="w-24 rounded bg-camwosa-bg px-2 py-1"
            />
          </label>
          <label>
            <span className="block text-camwosa-muted">dY (mm)</span>
            <input
              type="number"
              value={dy}
              onChange={(e) => setDy(Number(e.target.value))}
              step={1}
              className="w-24 rounded bg-camwosa-bg px-2 py-1"
            />
          </label>
          <button
            className="rounded border border-camwosa-default px-3 py-1 hover:bg-camwosa-overlay"
            onClick={anwenden_verschieben}
            disabled={dx === 0 && dy === 0}
          >
            Verschieben
          </button>
        </div>
      </section>

      {/* Rotieren */}
      <section className="space-y-2">
        <div className="text-xs font-semibold text-camwosa-muted uppercase tracking-wider">
          Design-Rotation (vor dem Wickeln)
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label>
            <span className="block text-camwosa-muted">Winkel (°)</span>
            <input
              type="number"
              value={rotGrad}
              onChange={(e) => setRotGrad(Number(e.target.value))}
              step={15}
              className="w-24 rounded bg-camwosa-bg px-2 py-1"
            />
          </label>
          <button
            className="rounded border border-camwosa-default px-3 py-1 hover:bg-camwosa-overlay"
            onClick={anwenden_rotieren}
            disabled={rotGrad === 0}
          >
            Rotieren
          </button>
          <span className="text-[10px] text-camwosa-muted">
            (rotiert das ABGEWICKELTE Design — z.B. um Schrift schraeg zu stellen)
          </span>
        </div>
      </section>
    </div>
  );
}
