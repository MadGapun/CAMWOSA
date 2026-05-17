import { useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import VoxelPreview3D from "../components/VoxelPreview3D";
import { CoachMark } from "../components/Tooltip";

interface SimErgebnis {
  aufloesung_mm: number;
  nx: number; ny: number; nz: number;
  werkstueck: { laenge_x: number; breite_y: number; hoehe_z: number };
  boundary_voxel: Array<[number, number, number]>;
  voxel_count: number;
  voxel_volumen_mm3: number;
  abgetragenes_volumen_mm3: number;
  bewegungen_simuliert: number;
}

/**
 * Voll-Material-Abtrag-Simulation auf Voxel-Basis.
 *
 * Im Gegensatz zur leichten `Simulation3D` (zeigt nur Toolpath-Linien) zeigt
 * diese View das Werkstueck nach dem Job — also was vom Material uebrig
 * bleibt. Wenn Markus's Schale ueber 4 Operationen gefraest wurde, sieht
 * man hier das fertige Werkstueck.
 */
export default function MaterialAbtragView() {
  const operationen = useAppStore((s) => s.operationen);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const aktiveOps = operationen.filter((o) => o.aktiviert && o.toolpath);

  const [aufloesung, setAufloesung] = useState(2.0);
  const [werkstueckBreite, setWerkstueckBreite] = useState(200);
  const [werkstueckLaenge, setWerkstueckLaenge] = useState(200);
  const [werkstueckHoehe, setWerkstueckHoehe] = useState(20);
  const [ergebnis, setErgebnis] = useState<SimErgebnis | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function simulieren() {
    if (!aktiveOps.length) {
      setFehler('Keine berechneten Toolpaths. Operationen anlegen und „Toolpath berechnen" klicken.');
      return;
    }
    // Werkzeug — bevorzugt das des ersten Toolpaths
    const werkzeug_id = aktiveOps[0].werkzeug_id;
    if (!werkzeuge.find((w) => w.id === werkzeug_id)) {
      setFehler(`Werkzeug '${werkzeug_id}' nicht in der Bibliothek.`);
      return;
    }
    setBusy(true); setFehler(null);
    try {
      const r = await camwosaApi.voxelSimulation(
        aktiveOps.map((o) => o.toolpath!),
        werkzeug_id,
        {
          laenge_x: werkstueckLaenge,
          breite_y: werkstueckBreite,
          hoehe_z: werkstueckHoehe,
        },
        aufloesung,
      );
      setErgebnis(r as SimErgebnis);
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Simulation fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  // Geschaetzte Voxel-Anzahl fuer Warnungen
  const geschVoxel = (
    (werkstueckLaenge / aufloesung) *
    (werkstueckBreite / aufloesung) *
    (werkstueckHoehe / aufloesung)
  );
  const heavy = geschVoxel > 5_000_000;

  return (
    <div className="space-y-4">
      <header>
        <CoachMark
          id="materialabtrag_intro"
          text="Diese View zeigt das Werkstueck NACH dem Job — also was vom Material uebrig bleibt. Im Gegensatz zur Simulation3D-View (nur Toolpath-Linien)."
          ablauf_tage={60}
        >
          <h1 className="text-xl font-bold">Material-Abtrag-Simulation</h1>
        </CoachMark>
        <p className="text-sm text-camwosa-muted">
          Voxel-basiert. Werkstueck wird in Wuerfel der Kantenlaenge
          „Aufloesung" zerlegt, jeder Werkzeug-Eingriff entfernt die
          eingeschlossenen Voxel. Boundary-Voxel werden gerendert.
        </p>
      </header>

      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Setup</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Num label="Werkstueck Laenge X (mm)" v={werkstueckLaenge} on={setWerkstueckLaenge} step={10} />
          <Num label="Werkstueck Breite Y (mm)" v={werkstueckBreite} on={setWerkstueckBreite} step={10} />
          <Num label="Werkstueck Hoehe Z (mm)" v={werkstueckHoehe} on={setWerkstueckHoehe} step={1} />
          <Num label="Aufloesung (mm)" v={aufloesung} on={setAufloesung} step={0.5} min={0.5} max={10} />
        </div>
        <div className="mt-2 text-xs text-camwosa-muted">
          Voxel-Schaetzung: <span className="font-mono">{geschVoxel.toLocaleString("de-DE", { maximumFractionDigits: 0 })}</span>
          {heavy && <span className="ml-2 text-camwosa-warn">⚠ heavy — groessere Aufloesung waehlen</span>}
        </div>
        <div className="mt-2 text-xs text-camwosa-muted">
          {aktiveOps.length} aktive Toolpath(s) zur Simulation
        </div>
      </section>

      <div className="flex items-center gap-2">
        <button
          className="rounded bg-camwosa-accent px-4 py-2 font-medium text-camwosa-bg hover:opacity-90 disabled:opacity-50"
          onClick={() => void simulieren()}
          disabled={busy || aktiveOps.length === 0}
        >
          {busy ? "Simuliere..." : "→ Material-Abtrag simulieren"}
        </button>
        {ergebnis && (
          <span className="text-xs text-camwosa-muted">
            {ergebnis.voxel_count.toLocaleString("de-DE")} Boundary-Voxel ·{" "}
            <span className="text-camwosa-ok">{ergebnis.abgetragenes_volumen_mm3.toFixed(0)} mm³ abgetragen</span> ·{" "}
            Restmaterial {ergebnis.voxel_volumen_mm3.toFixed(0)} mm³
          </span>
        )}
      </div>

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
          {fehler}
        </div>
      )}

      {ergebnis && (
        <VoxelPreview3D
          boundaryVoxel={ergebnis.boundary_voxel}
          aufloesungMm={ergebnis.aufloesung_mm}
          werkstueck={ergebnis.werkstueck}
          hoehe={500}
        />
      )}
    </div>
  );
}

function Num({
  label, v, on, step, min, max,
}: { label: string; v: number; on: (n: number) => void; step: number; min?: number; max?: number }) {
  return (
    <label className="text-xs">
      <span className="mb-0.5 block text-camwosa-muted">{label}</span>
      <input
        type="number"
        value={v}
        step={step}
        min={min} max={max}
        onChange={(e) => on(Number(e.target.value))}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
    </label>
  );
}
