import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import type { Material, Werkzeug } from "../api/types";
import { FachTooltip } from "../components/Tooltip";
import { FACHBEGRIFFE } from "../components/fachbegriffe";

const OP_LABELS: Record<string, string> = {
  generic: "Generisch (Fallback)",
  kontur: "Kontur",
  tasche: "Tasche",
  gravur: "Gravur",
  bohren: "Bohren",
  relief: "Relief",
  schruppen: "Schruppen",
  schlichten: "Schlichten",
};

interface Preset {
  id: string;
  name: string;
  material_id: string;
  werkzeug_id: string;
  operation_typ: string;
  rpm: number;
  vorschub: number;
  plunge: number;
  stepdown: number;
  stepover_prozent: number;
  notizen?: string;
}

interface Props {
  material: Material;
  werkzeuge: Werkzeug[];
}

export default function CuttingPresetEditor({ material, werkzeuge }: Props) {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [neu, setNeu] = useState<Partial<Preset>>({
    operation_typ: "generic",
  });
  const [fehler, setFehler] = useState<string | null>(null);

  async function reload() {
    const r = await camwosaApi.cuttingPresets({ material_id: material.id });
    setPresets(r);
  }

  useEffect(() => { void reload(); }, [material.id]);

  async function speichern() {
    setFehler(null);
    if (!neu.werkzeug_id) {
      setFehler("Werkzeug auswaehlen");
      return;
    }
    const id = `${material.id}__${neu.werkzeug_id}__${neu.operation_typ ?? "generic"}`;
    const payload: Preset = {
      id,
      name: neu.name || "",
      material_id: material.id,
      werkzeug_id: neu.werkzeug_id,
      operation_typ: neu.operation_typ ?? "generic",
      rpm: Number(neu.rpm ?? 18000),
      vorschub: Number(neu.vorschub ?? 1500),
      plunge: Number(neu.plunge ?? 300),
      stepdown: Number(neu.stepdown ?? 1.0),
      stepover_prozent: Number(neu.stepover_prozent ?? 40),
      notizen: neu.notizen,
    };
    try {
      await camwosaApi.cuttingPresetSpeichern(payload);
      setNeu({ operation_typ: "generic" });
      await reload();
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Speichern fehlgeschlagen");
    }
  }

  async function loeschen(p: Preset) {
    if (!window.confirm(`Preset '${p.name || p.id}' loeschen?`)) return;
    try {
      await camwosaApi.cuttingPresetLoeschen(p.id);
      await reload();
    } catch (e: any) {
      const msg = e.response?.data?.fehler ?? e.message;
      window.alert(`Loeschen fehlgeschlagen: ${msg}\n\n(Legacy-Presets aus Material.presets[] sind nicht direkt loeschbar — Override mit gleicher ID anlegen.)`);
    }
  }

  return (
    <div className="space-y-3 text-sm">
      <h4 className="font-semibold">Schnittparameter ({presets.length})</h4>

      <table className="w-full text-xs">
        <thead className="border-b border-gray-700 text-left uppercase text-camwosa-muted">
          <tr>
            <th className="py-1">Werkzeug</th>
            <th>Operation</th>
            <th>RPM</th>
            <th>Vorschub<FachTooltip {...FACHBEGRIFFE.vorschub} /></th>
            <th>Plunge<FachTooltip {...FACHBEGRIFFE.plunge} /></th>
            <th>Stepdown<FachTooltip {...FACHBEGRIFFE.stepdown} /></th>
            <th>Stepover<FachTooltip {...FACHBEGRIFFE.stepover} /></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {presets.map((p) => {
            const wz = werkzeuge.find((w) => w.id === p.werkzeug_id);
            return (
              <tr key={p.id} className="border-b border-gray-800">
                <td className="py-1">{wz?.name ?? p.werkzeug_id}</td>
                <td>{OP_LABELS[p.operation_typ] ?? p.operation_typ}</td>
                <td>{p.rpm}</td>
                <td>{p.vorschub}</td>
                <td>{p.plunge}</td>
                <td>{p.stepdown}</td>
                <td>{p.stepover_prozent}%</td>
                <td>
                  <button
                    className="rounded border border-red-700 px-2 py-0.5 hover:bg-red-900/40"
                    onClick={() => void loeschen(p)}
                  >
                    🗑
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="rounded border border-gray-700 bg-camwosa-bg p-3">
        <h5 className="mb-2 text-xs font-semibold uppercase text-camwosa-muted">
          Neues Preset
        </h5>
        <div className="grid grid-cols-4 gap-2 text-xs">
          <select
            className="rounded bg-camwosa-surface px-2 py-1"
            value={neu.werkzeug_id ?? ""}
            onChange={(e) => setNeu({ ...neu, werkzeug_id: e.target.value })}
          >
            <option value="">-- Werkzeug --</option>
            {werkzeuge.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
          <select
            className="rounded bg-camwosa-surface px-2 py-1"
            value={neu.operation_typ ?? "generic"}
            onChange={(e) => setNeu({ ...neu, operation_typ: e.target.value })}
          >
            {Object.entries(OP_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <NumIn p="RPM" v={neu.rpm} on={(n) => setNeu({ ...neu, rpm: n ?? undefined })} />
          <NumIn p="Vorschub" v={neu.vorschub} on={(n) => setNeu({ ...neu, vorschub: n ?? undefined })} />
          <NumIn p="Plunge" v={neu.plunge} on={(n) => setNeu({ ...neu, plunge: n ?? undefined })} />
          <NumIn p="Stepdown" v={neu.stepdown} on={(n) => setNeu({ ...neu, stepdown: n ?? undefined })} />
          <NumIn p="Stepover%" v={neu.stepover_prozent}
            on={(n) => setNeu({ ...neu, stepover_prozent: n ?? undefined })} />
          <button
            className="rounded bg-camwosa-accent px-2 py-1 font-medium text-camwosa-bg hover:opacity-90"
            onClick={() => void speichern()}
          >
            + Speichern
          </button>
        </div>
        {fehler && (
          <div className="mt-2 text-xs text-red-400">{fehler}</div>
        )}
      </div>
    </div>
  );
}

function NumIn({
  p, v, on,
}: { p: string; v: number | undefined; on: (n: number | null) => void }) {
  return (
    <input
      type="number"
      placeholder={p}
      className="rounded bg-camwosa-surface px-2 py-1"
      value={v ?? ""}
      onChange={(e) => on(e.target.value === "" ? null : Number(e.target.value))}
    />
  );
}
