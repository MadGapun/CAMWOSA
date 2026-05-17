import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";
import type { Werkzeug, WerkzeugTyp } from "../api/types";
import Modal from "../components/Modal";
import WerkzeugEditor from "../editor/WerkzeugEditor";
import { camwosaApi } from "../api/client";

const TYP_LABELS: Record<WerkzeugTyp, string> = {
  schaftfraeser: "Schaftfraeser",
  kugelfraeser: "Kugelfraeser",
  torusfraeser: "Torusfraeser",
  v_bit: "V-Bit",
  gravierstichel: "Gravierstichel",
  bohrer: "Bohrer",
  einschneider: "Einschneider",
  fischschwanz: "Fischschwanz",
  schruppfraeser: "Schruppfraeser",
  diamantgravierer: "Diamantgravierer",
};

export default function WerkzeugeView() {
  const { t } = useTranslation();
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const setWerkzeuge = useAppStore((s) => s.setWerkzeuge);
  const materialien = useAppStore((s) => s.materialien);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [editMode, setEditMode] = useState<"none" | "neu" | "bearbeiten">("none");
  const [filterTyp, setFilterTyp] = useState<WerkzeugTyp | "">("");
  const [standzeit, setStandzeit] = useState<Record<string, {
    genutzt_minuten: number; max_minuten: number | null;
    prozent: number | null; warnung: boolean; kritisch: boolean;
  }>>({});

  async function reloadStandzeit() {
    try {
      const liste = await camwosaApi.standzeitListe();
      const map: typeof standzeit = {};
      for (const s of liste) {
        map[s.werkzeug_id] = {
          genutzt_minuten: s.genutzt_minuten,
          max_minuten: s.max_minuten,
          prozent: s.prozent,
          warnung: s.warnung,
          kritisch: s.kritisch,
        };
      }
      setStandzeit(map);
    } catch { /* Standzeit-API optional */ }
  }

  useEffect(() => { void reloadStandzeit(); }, [werkzeuge.length]);

  async function standzeitReset(w: Werkzeug) {
    if (!window.confirm(`Standzeit fuer '${w.name}' wirklich zuruecksetzen?`)) return;
    await camwosaApi.standzeitReset(w.id);
    await reloadStandzeit();
  }

  async function reload() {
    setWerkzeuge(await camwosaApi.werkzeuge());
  }

  async function loeschen(w: Werkzeug) {
    if (!window.confirm(`Werkzeug '${w.name}' wirklich loeschen?`)) return;
    try {
      await camwosaApi.werkzeugLoeschen(w.id);
      await reload();
    } catch (e: any) {
      const msg = e.response?.data?.fehler ?? e.message;
      window.alert(`Loeschen fehlgeschlagen: ${msg}`);
    }
  }

  const detail = werkzeuge.find((w) => w.id === detailId) ?? null;
  const gefiltert = werkzeuge.filter(
    (w) => !filterTyp || w.typ === filterTyp,
  );

  async function exportWerkzeug(w: Werkzeug) {
    const r = await fetch(`/api/tools/${w.id}/export`).then((r) => r.json());
    const blob = new Blob([JSON.stringify(r, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${w.id}.camwosa-tool.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("navigation.werkzeuge")}</h1>
        <div className="flex items-center gap-2">
          <select
            className="rounded bg-camwosa-bg px-3 py-1 text-sm"
            value={filterTyp}
            onChange={(e) => setFilterTyp(e.target.value as WerkzeugTyp | "")}
          >
            <option value="">Alle Typen</option>
            {Object.entries(TYP_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-sm font-medium text-camwosa-bg hover:opacity-90"
            onClick={() => { setDetailId(null); setEditMode("neu"); }}
          >
            + Neues Werkzeug
          </button>
        </div>
      </div>

      <table className="w-full text-sm">
        <thead className="border-b border-gray-700 text-left text-xs uppercase text-camwosa-muted">
          <tr>
            <th className="py-2">Name</th>
            <th>Typ</th>
            <th>Durchmesser</th>
            <th>Schneiden</th>
            <th>Schneidlaenge</th>
            <th>Standzeit</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {gefiltert.map((w) => (
            <tr key={w.id} className="border-b border-gray-800 hover:bg-camwosa-surface">
              <td className="py-2 cursor-pointer" onClick={() => setDetailId(w.id)}>
                <span className="font-medium">{w.name}</span>
              </td>
              <td>{TYP_LABELS[w.typ]}</td>
              <td>{w.durchmesser} mm</td>
              <td>{w.schneiden}</td>
              <td>{w.schneidlaenge} mm</td>
              <td className="text-xs">
                <StandzeitZelle
                  werkzeug={w}
                  status={standzeit[w.id]}
                  onReset={() => void standzeitReset(w)}
                />
              </td>
              <td className="space-x-1 whitespace-nowrap">
                <button
                  className="rounded border border-gray-600 px-2 py-0.5 text-xs hover:bg-gray-700"
                  onClick={() => { setDetailId(w.id); setEditMode("bearbeiten"); }}
                  title="Bearbeiten"
                >
                  ✏
                </button>
                <button
                  className="rounded border border-gray-600 px-2 py-0.5 text-xs hover:bg-gray-700"
                  onClick={() => void exportWerkzeug(w)}
                  title="Als JSON exportieren"
                >
                  📦
                </button>
                <button
                  className="rounded border border-red-700 px-2 py-0.5 text-xs hover:bg-red-900/40"
                  onClick={() => void loeschen(w)}
                  title="Loeschen"
                >
                  🗑
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Modal
        open={editMode !== "none"}
        onClose={() => setEditMode("none")}
        titel={editMode === "neu" ? "Neues Werkzeug" : "Werkzeug bearbeiten"}
        breit
      >
        <WerkzeugEditor
          initial={editMode === "bearbeiten" ? detail : null}
          onAbbrechen={() => setEditMode("none")}
          onGespeichert={async () => {
            await reload();
            setEditMode("none");
          }}
        />
      </Modal>

      <Modal
        open={detail !== null}
        onClose={() => setDetailId(null)}
        titel={detail ? `Werkzeug: ${detail.name}` : ""}
        breit
      >
        {detail && <WerkzeugDetail werkzeug={detail} materialien={materialien} />}
      </Modal>
    </div>
  );
}

function WerkzeugDetail({
  werkzeug,
  materialien,
}: {
  werkzeug: Werkzeug;
  materialien: ReturnType<typeof useAppStore.getState>["materialien"];
}) {
  const presetsProMaterial = materialien
    .map((m) => ({
      material: m,
      preset: m.presets.find((p) => p.werkzeug_id === werkzeug.id),
    }))
    .filter((x) => x.preset !== undefined);

  return (
    <div className="space-y-4 text-sm">
      <section>
        <h3 className="mb-2 font-semibold">Geometrie</h3>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <Feld label="Typ" wert={TYP_LABELS[werkzeug.typ]} />
          <Feld label="ID" wert={werkzeug.id} />
          <Feld label="Material" wert={werkzeug.material ?? "?"} />
          <Feld label="Beschichtung" wert={werkzeug.beschichtung ?? "keine"} />
          <Feld label="Schneid-Ø" wert={`${werkzeug.durchmesser} mm`} />
          <Feld label="Schaft-Ø" wert={`${werkzeug.schaft_durchmesser} mm`} />
          <Feld label="Schneidlaenge" wert={`${werkzeug.schneidlaenge} mm`} />
          <Feld label="Gesamtlaenge" wert={`${werkzeug.gesamtlaenge} mm`} />
          <Feld label="Schneiden" wert={`${werkzeug.schneiden}`} />
          {werkzeug.spitzenwinkel != null && (
            <Feld label="Spitzenwinkel" wert={`${werkzeug.spitzenwinkel}°`} />
          )}
          {werkzeug.spitzenradius != null && (
            <Feld label="Spitzenradius" wert={`${werkzeug.spitzenradius} mm`} />
          )}
          {werkzeug.standzeit_max_minuten != null && (
            <Feld label="Standzeit (geplant)" wert={`${werkzeug.standzeit_max_minuten} min`} />
          )}
        </div>
        {werkzeug.notizen && (
          <p className="mt-2 rounded bg-camwosa-bg p-2 text-xs italic text-camwosa-muted">
            {werkzeug.notizen}
          </p>
        )}
      </section>

      <section>
        <h3 className="mb-2 font-semibold">
          Material-Presets ({presetsProMaterial.length})
        </h3>
        {presetsProMaterial.length === 0 ? (
          <p className="text-xs text-camwosa-muted">
            Keine Presets fuer dieses Werkzeug definiert.
          </p>
        ) : (
          <table className="w-full text-xs">
            <thead className="border-b border-gray-700 text-left uppercase text-camwosa-muted">
              <tr>
                <th className="py-1">Material</th>
                <th>RPM</th>
                <th>Vorschub</th>
                <th>Plunge</th>
                <th>Stepdown</th>
                <th>Stepover</th>
              </tr>
            </thead>
            <tbody>
              {presetsProMaterial.map(({ material, preset }) => (
                <tr key={material.id} className="border-b border-gray-800">
                  <td className="py-1">{material.name}</td>
                  <td>{preset!.rpm}</td>
                  <td>{preset!.vorschub} mm/min</td>
                  <td>{preset!.plunge} mm/min</td>
                  <td>{preset!.stepdown} mm</td>
                  <td>{preset!.stepover_prozent}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="mt-2 text-xs text-camwosa-muted">
          Presets werden in den Material-JSON-Dateien gepflegt
          (<code>data/materials/</code>). Editier-UI folgt.
        </p>
      </section>
    </div>
  );
}

function StandzeitZelle({
  werkzeug, status, onReset,
}: {
  werkzeug: Werkzeug;
  status?: {
    genutzt_minuten: number; max_minuten: number | null;
    prozent: number | null; warnung: boolean; kritisch: boolean;
  };
  onReset: () => void;
}) {
  if (!werkzeug.standzeit_max_minuten) {
    return <span className="text-camwosa-muted">—</span>;
  }
  const genutzt = status?.genutzt_minuten ?? 0;
  const prozent = status?.prozent ?? 0;
  const farbe = status?.kritisch
    ? "bg-camwosa-danger"
    : status?.warnung
    ? "bg-camwosa-warn"
    : "bg-camwosa-ok";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-16 overflow-hidden rounded bg-camwosa-inset">
        <div
          className={`h-full ${farbe}`}
          style={{ width: `${Math.min(100, prozent)}%` }}
        />
      </div>
      <span className="font-mono text-[10px]" title={`${genutzt.toFixed(1)} / ${werkzeug.standzeit_max_minuten} min`}>
        {prozent.toFixed(0)}%
      </span>
      <button
        className="rounded border border-camwosa-default px-1 text-[10px] text-camwosa-muted hover:text-camwosa-text"
        onClick={(e) => { e.stopPropagation(); onReset(); }}
        title="Standzeit zuruecksetzen (Werkzeug ausgetauscht)"
      >
        ↺
      </button>
    </div>
  );
}

function Feld({ label, wert }: { label: string; wert: string }) {
  return (
    <div>
      <div className="text-camwosa-muted">{label}</div>
      <div className="font-mono">{wert}</div>
    </div>
  );
}
