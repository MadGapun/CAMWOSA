import { useState } from "react";
import { camwosaApi } from "../api/client";

/**
 * Filter-Stack-Panel fuer die Heightmap-Bearbeitung (Master-Plan D25 / A35).
 *
 * Der User stapelt Filter (Gamma, Zero-Plane, Edge-Boost, ...) und klickt
 * „Anwenden", dann lauft die Liste vom Anfang durch und liefert eine neue
 * Heightmap. Jeder Filter ist toggle-bar — so kann der User Effekte
 * dazuschalten ohne den Stack zu zerstoeren.
 *
 * Reset-Button setzt die Filter-Liste zurueck. Der originale Heightmap-Wert
 * wird vom Parent (BildReliefView) verwaltet, dieser Component bekommt sie
 * als Prop + ein Callback fuer das Ergebnis.
 */

type FilterTyp =
  | "gamma"
  | "histogramm-stretch"
  | "zero-plane"
  | "edge-boost"
  | "selective-smoothing"
  | "detail-slider";

interface FilterEintrag {
  id: string;
  typ: FilterTyp;
  enabled: boolean;
  parameter: Record<string, unknown>;
}

const DEFAULT_PARAMETER: Record<FilterTyp, Record<string, unknown>> = {
  "gamma": { gamma: 1.2 },
  "histogramm-stretch": { low_perzentil: 2, high_perzentil: 98 },
  "zero-plane": { schwelle: 0.85 },
  "edge-boost": { faktor: 0.5 },
  "selective-smoothing": { radius: 1, bereich: "alles", schwelle: 0.5 },
  "detail-slider": { detail: 0.5 },
};

const FILTER_LABELS: Record<FilterTyp, string> = {
  "gamma": "Gamma-Korrektur",
  "histogramm-stretch": "Histogramm-Stretch",
  "zero-plane": "Zero-Plane (Sockel)",
  "edge-boost": "Edge-Boost",
  "selective-smoothing": "Selective Smoothing",
  "detail-slider": "Detail-Slider",
};

interface Props {
  originalHeightmap: unknown;
  onErgebnis: (gefiltert: unknown) => void;
}

export default function HeightmapFilterStack({
  originalHeightmap, onErgebnis,
}: Props) {
  const [filter, setFilter] = useState<FilterEintrag[]>([]);
  const [busy, setBusy] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  function hinzufuegen(typ: FilterTyp) {
    setFilter((prev) => [
      ...prev,
      {
        id: `f_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        typ,
        enabled: true,
        parameter: { ...DEFAULT_PARAMETER[typ] },
      },
    ]);
  }

  function entfernen(id: string) {
    setFilter((prev) => prev.filter((f) => f.id !== id));
  }

  function verschieben(id: string, richtung: -1 | 1) {
    setFilter((prev) => {
      const idx = prev.findIndex((f) => f.id === id);
      if (idx < 0) return prev;
      const next = idx + richtung;
      if (next < 0 || next >= prev.length) return prev;
      const kopie = [...prev];
      [kopie[idx], kopie[next]] = [kopie[next], kopie[idx]];
      return kopie;
    });
  }

  function toggle(id: string) {
    setFilter((prev) =>
      prev.map((f) => (f.id === id ? { ...f, enabled: !f.enabled } : f)),
    );
  }

  function parameterSetzen(id: string, key: string, wert: unknown) {
    setFilter((prev) =>
      prev.map((f) =>
        f.id === id
          ? { ...f, parameter: { ...f.parameter, [key]: wert } }
          : f,
      ),
    );
  }

  async function anwenden() {
    if (!originalHeightmap) {
      setFehler("Keine Heightmap vorhanden");
      return;
    }
    setBusy(true);
    setFehler(null);
    try {
      let aktuell = originalHeightmap;
      for (const f of filter) {
        if (!f.enabled) continue;
        aktuell = await camwosaApi.heightmapFilter(f.typ, aktuell, f.parameter);
      }
      onErgebnis(aktuell);
    } catch (e: unknown) {
      const msg = e instanceof Error
        ? e.message
        : ((e as { response?: { data?: { fehler?: string } } })?.response?.data?.fehler
            ?? String(e));
      setFehler(msg);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setFilter([]);
    onErgebnis(originalHeightmap);
  }

  return (
    <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Filter-Stack (Phase D)</h2>
        <span className="text-xs text-camwosa-muted">
          {filter.length === 0 ? "Keine Filter aktiv" : `${filter.length} Filter`}
        </span>
      </div>

      {/* Filter-Liste */}
      <div className="space-y-2">
        {filter.map((f, idx) => (
          <div
            key={f.id}
            className={`rounded border border-camwosa-default p-2 text-xs ${
              f.enabled ? "" : "opacity-50"
            }`}
          >
            <div className="mb-1 flex items-center justify-between gap-2">
              <label className="flex items-center gap-2 font-medium">
                <input
                  type="checkbox"
                  checked={f.enabled}
                  onChange={() => toggle(f.id)}
                />
                <span>
                  {idx + 1}. {FILTER_LABELS[f.typ]}
                </span>
              </label>
              <div className="flex items-center gap-1">
                <button
                  className="rounded border border-camwosa-default px-1 hover:bg-camwosa-bg disabled:opacity-30"
                  onClick={() => verschieben(f.id, -1)}
                  disabled={idx === 0}
                  title="Nach oben"
                >
                  ↑
                </button>
                <button
                  className="rounded border border-camwosa-default px-1 hover:bg-camwosa-bg disabled:opacity-30"
                  onClick={() => verschieben(f.id, 1)}
                  disabled={idx === filter.length - 1}
                  title="Nach unten"
                >
                  ↓
                </button>
                <button
                  className="rounded border border-red-700 px-1 text-red-300 hover:bg-red-900/40"
                  onClick={() => entfernen(f.id)}
                  title="Entfernen"
                >
                  ✕
                </button>
              </div>
            </div>
            <FilterParameter f={f} onChange={(k, v) => parameterSetzen(f.id, k, v)} />
          </div>
        ))}
      </div>

      {/* Filter hinzufuegen */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <select
          className="rounded border border-camwosa-default bg-camwosa-bg px-2 py-1 text-xs"
          defaultValue=""
          onChange={(e) => {
            if (e.target.value) {
              hinzufuegen(e.target.value as FilterTyp);
              e.target.value = "";
            }
          }}
        >
          <option value="">+ Filter hinzufuegen ...</option>
          {(Object.keys(FILTER_LABELS) as FilterTyp[]).map((typ) => (
            <option key={typ} value={typ}>{FILTER_LABELS[typ]}</option>
          ))}
        </select>
        <button
          className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
          onClick={() => void anwenden()}
          disabled={busy || filter.length === 0 || !originalHeightmap}
        >
          {busy ? "Wende an..." : "Anwenden"}
        </button>
        <button
          className="rounded border border-camwosa-default px-3 py-1 text-xs hover:bg-camwosa-bg"
          onClick={reset}
        >
          Stack zuruecksetzen
        </button>
      </div>

      {fehler && (
        <p className="mt-2 text-xs text-camwosa-danger">⚠ {fehler}</p>
      )}
    </section>
  );
}


function FilterParameter({
  f, onChange,
}: { f: FilterEintrag; onChange: (key: string, v: unknown) => void }) {
  const p = f.parameter;
  switch (f.typ) {
    case "gamma":
      return (
        <NumParam label="γ (>1 dunkler, <1 heller)" wert={p.gamma as number}
                  onChange={(v) => onChange("gamma", v)} step={0.1} min={0.1} />
      );
    case "histogramm-stretch":
      return (
        <div className="flex gap-2">
          <NumParam label="Low %" wert={p.low_perzentil as number}
                    onChange={(v) => onChange("low_perzentil", v)} step={1} min={0} max={49} />
          <NumParam label="High %" wert={p.high_perzentil as number}
                    onChange={(v) => onChange("high_perzentil", v)} step={1} min={51} max={100} />
        </div>
      );
    case "zero-plane":
      return (
        <NumParam label="Helligkeits-Schwelle (0..1)" wert={p.schwelle as number}
                  onChange={(v) => onChange("schwelle", v)} step={0.05} min={0} max={1} />
      );
    case "edge-boost":
      return (
        <NumParam label="Faktor (0=aus, 1=voll)" wert={p.faktor as number}
                  onChange={(v) => onChange("faktor", v)} step={0.1} min={0} max={3} />
      );
    case "selective-smoothing":
      return (
        <div className="flex flex-wrap gap-2">
          <NumParam label="Radius (Pixel)" wert={p.radius as number}
                    onChange={(v) => onChange("radius", Math.round(v))} step={1} min={0} max={10} />
          <label className="text-xs">
            <span className="mb-0.5 block text-camwosa-muted">Bereich</span>
            <select
              value={p.bereich as string}
              onChange={(e) => onChange("bereich", e.target.value)}
              className="rounded border border-camwosa-default bg-camwosa-bg px-2 py-1"
            >
              <option value="alles">alles</option>
              <option value="hell">nur hell</option>
              <option value="dunkel">nur dunkel</option>
            </select>
          </label>
          {p.bereich !== "alles" && (
            <NumParam label="Schwelle" wert={p.schwelle as number}
                      onChange={(v) => onChange("schwelle", v)} step={0.05} min={0} max={1} />
          )}
        </div>
      );
    case "detail-slider":
      return (
        <NumParam label="Detail (-1 weich ... +1 scharf)" wert={p.detail as number}
                  onChange={(v) => onChange("detail", v)} step={0.1} min={-1} max={1} />
      );
  }
}


function NumParam({
  label, wert, onChange, step, min, max,
}: { label: string; wert: number; onChange: (v: number) => void;
     step: number; min?: number; max?: number }) {
  return (
    <label className="text-xs">
      <span className="mb-0.5 block text-camwosa-muted">{label}</span>
      <input
        type="number"
        value={wert}
        step={step}
        min={min} max={max}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-24 rounded bg-camwosa-bg px-2 py-1"
      />
    </label>
  );
}
