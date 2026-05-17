import { useEffect, useMemo, useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import WrapDesignEditor, { type WrapPunkt } from "../editor/WrapDesignEditor";
import WrapPatternTransform from "../editor/WrapPatternTransform";
import WrapPreview3D from "../components/WrapPreview3D";
import { CoachMark } from "../components/Tooltip";
import type { Toolpath } from "../api/types";

const VORLAGEN: Record<string, WrapPunkt[]> = {
  rechteck_50x40: [[0, 0], [50, 0], [50, 40], [0, 40], [0, 0]],
  diagonale_50: [[0, 0], [50, 50]],
  spirale_kurz: [[0, 0], [10, 20], [20, 40], [30, 60], [40, 80]],
  linie_30: [[0, 0], [30, 0]],
};

/**
 * Wrap-Mode-View: 2D-Pfad zeichnen + Live-3D-Vorschau auf Zylinder + G-Code erzeugen.
 *
 * Workflow:
 * 1. Werkstueck-Radius festlegen
 * 2. Pfad in der abgewickelten 2D-Ansicht zeichnen (Klick = Punkt, Drag = verschieben)
 * 3. 3D-Vorschau zeigt sofort wie das Design auf dem Zylinder aussieht
 * 4. Pruef-Run gegen den Werkstueck-Umfang
 * 5. Toolpath erzeugen — landet im App-Store als Operation
 */
export default function WrapView() {
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const operationHinzufuegen = useAppStore((s) => s.operationHinzufuegen);

  const [punkte, setPunkte] = useState<WrapPunkt[]>(VORLAGEN.rechteck_50x40);
  const [werkzeugId, setWerkzeugId] = useState(werkzeuge[0]?.id ?? "");
  const [werkstueckRadius, setWerkstueckRadius] = useState(20);
  const [werkstueckLaenge, setWerkstueckLaenge] = useState(100);
  const [spindelRpm, setSpindelRpm] = useState(18000);
  const [vorschub, setVorschub] = useState(800);
  const [eintauchVorschub, setEintauchVorschub] = useState(250);
  const [maxTiefe, setMaxTiefe] = useState(0.5);
  const [stepdown, setStepdown] = useState(0.5);
  const [geschlossen, setGeschlossen] = useState(true);

  const [tp, setTp] = useState<Toolpath | null>(null);
  const [warnungen, setWarnungen] = useState<string[]>([]);
  const [fehler, setFehler] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Live-Pruefung des Designs
  useEffect(() => {
    const id = setTimeout(() => {
      void (async () => {
        try {
          const r = await camwosaApi.opWrapPruefe(punkte, werkstueckRadius);
          setWarnungen(r.warnungen);
        } catch { /* ignore */ }
      })();
    }, 300);
    return () => clearTimeout(id);
  }, [punkte, werkstueckRadius]);

  const umfang = useMemo(() => 2 * Math.PI * werkstueckRadius, [werkstueckRadius]);

  async function erzeugen() {
    if (!werkzeugId) { setFehler("Werkzeug waehlen"); return; }
    if (punkte.length < 2) { setFehler("Mindestens 2 Punkte"); return; }
    setBusy(true); setFehler(null);
    try {
      const result = await camwosaApi.opWrap(werkzeugId, punkte, {
        werkzeug_id: werkzeugId,
        spindel_rpm: spindelRpm,
        vorschub,
        eintauch_vorschub: eintauchVorschub,
        sicherheitshoehe: 5,
        werkstueck_radius_mm: werkstueckRadius,
        max_tiefe: maxTiefe,
        stepdown,
        geschlossen,
      });
      setTp(result);
      operationHinzufuegen({
        id: `wrap_${Date.now()}`,
        name: `Wrap (${punkte.length} Pkt, Ø${(werkstueckRadius * 2).toFixed(0)}mm)`,
        typ: "gravur",
        werkzeug_id: werkzeugId,
        geometrie_id: null,
        parameter: { werkzeug_id: werkzeugId } as any,
        toolpath: result,
        aktiviert: true,
      });
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Fehler");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <CoachMark
          id="wrap_intro"
          text="Hier wickelst du ein 2D-Design auf einen Zylinder. X bleibt linear (Werkstueck-Laengsachse), Y wird in Bogenlaenge umgerechnet. Beispiel: Schriftzug auf eine Drechsel-Saeule."
          ablauf_tage={60}
        >
          <h1 className="text-xl font-bold">Wrap-Mode (2D auf Zylinder)</h1>
        </CoachMark>
        <p className="text-sm text-camwosa-muted">
          Y-Bewegungen werden automatisch in A-Achsen-Winkel umgerechnet
          (<span className="font-mono">A° = Y · 57.296 / Radius</span>).
          Fuer rotationssymmetrische Formgebung (Vase, Schale) → „Drechseln" stattdessen.
        </p>
      </header>

      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Werkstueck + Werkzeug</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Feld label="Werkzeug">
            <select
              value={werkzeugId}
              onChange={(e) => setWerkzeugId(e.target.value)}
              className="w-full rounded bg-camwosa-bg px-2 py-1"
            >
              <option value="">— waehlen —</option>
              {werkzeuge.map((w) => (
                <option key={w.id} value={w.id}>{w.name} ({w.durchmesser}mm)</option>
              ))}
            </select>
          </Feld>
          <Num label="Werkstueck-Ø/2 (mm)" v={werkstueckRadius} on={setWerkstueckRadius} step={0.5} />
          <Num label="Werkstueck-Laenge X (mm)" v={werkstueckLaenge} on={setWerkstueckLaenge} step={5} />
          <div className="text-xs text-camwosa-muted">
            <span className="block">Umfang:</span>
            <span className="font-mono text-base text-camwosa-text">{umfang.toFixed(1)} mm</span>
          </div>
        </div>
      </section>

      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Design (abgewickelt)</h2>
        <WrapDesignEditor
          punkte={punkte}
          onChange={setPunkte}
          werkstueck_radius_mm={werkstueckRadius}
        />
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="text-camwosa-muted">Klick = neuer Punkt am Ende · Drag = verschieben · Rechtsklick = löschen</span>
          <span className="grow"></span>
          {Object.keys(VORLAGEN).map((k) => (
            <button
              key={k}
              className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
              onClick={() => setPunkte(VORLAGEN[k])}
            >
              {k.replaceAll("_", " ")}
            </button>
          ))}
          <button
            className="rounded border border-red-700 px-2 py-1 hover:bg-red-900/40"
            onClick={() => setPunkte([])}
          >
            Leeren
          </button>
        </div>
        {warnungen.length > 0 && (
          <ul className="mt-2 space-y-0.5 text-xs text-camwosa-warn">
            {warnungen.map((w, i) => (
              <li key={i}>⚠ {w}</li>
            ))}
          </ul>
        )}
      </section>

      <WrapPatternTransform
        punkte={punkte}
        onChange={setPunkte}
        werkstueck_radius_mm={werkstueckRadius}
        werkstueck_laenge_mm={werkstueckLaenge}
      />

      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">3D-Vorschau (gewickelt)</h2>
        <WrapPreview3D
          punkte={punkte}
          werkstueck_radius_mm={werkstueckRadius}
          werkstueck_laenge_mm={werkstueckLaenge}
          hoehe={340}
        />
      </section>

      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Schnitt-Parameter</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <Num label="Spindel RPM" v={spindelRpm} on={setSpindelRpm} step={500} />
          <Num label="Vorschub (mm/min)" v={vorschub} on={setVorschub} step={50} />
          <Num label="Plunge (mm/min)" v={eintauchVorschub} on={setEintauchVorschub} step={50} />
          <Num label="Max Tiefe (mm)" v={maxTiefe} on={setMaxTiefe} step={0.1} />
          <Num label="Stepdown (mm)" v={stepdown} on={setStepdown} step={0.1} />
        </div>
        <label className="mt-3 flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={geschlossen}
            onChange={(e) => setGeschlossen(e.target.checked)}
          />
          <span>Geschlossener Pfad (Ende → Start)</span>
        </label>
      </section>

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
          {fehler}
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          className="rounded bg-camwosa-accent px-4 py-2 font-medium text-camwosa-bg hover:opacity-90 disabled:opacity-50"
          onClick={() => void erzeugen()}
          disabled={busy || punkte.length < 2 || !werkzeugId}
        >
          {busy ? "Erzeuge..." : "→ Wrap-Toolpath erzeugen"}
        </button>
        {tp && (
          <span className="text-xs text-camwosa-ok">
            ✓ {tp.bewegungen.length} Bewegungen — landet im Tab „Operationen"
          </span>
        )}
      </div>
    </div>
  );
}

function Feld({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-xs">
      <span className="mb-0.5 block text-camwosa-muted">{label}</span>
      {children}
    </label>
  );
}

function Num({
  label, v, on, step,
}: { label: string; v: number; on: (n: number) => void; step: number }) {
  return (
    <Feld label={label}>
      <input
        type="number"
        step={step}
        value={v}
        onChange={(e) => on(Number(e.target.value))}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
    </Feld>
  );
}
