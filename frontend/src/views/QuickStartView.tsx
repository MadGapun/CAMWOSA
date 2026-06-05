import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import { quickcamProjektInStores } from "../state/projektIO";
import { CoachMark } from "../components/Tooltip";

interface TemplateParameter {
  name: string;
  label: string;
  typ: string;
  default: unknown;
  einheit?: string;
  hinweis?: string;
}

interface QCTemplate {
  id: string;
  name: string;
  kurzbeschreibung: string;
  icon: string;
  operation_typ: string;
  parameter: TemplateParameter[];
}

/**
 * Quick-CAM-Einstieg: ein-Klick-Templates fuer haeufige Einzelfraesaufgaben.
 * Direkt nach App-Start sichtbar — wer mehr will, geht in die normale UI.
 */
export default function QuickStartView({ onErzeugt }: { onErzeugt?: () => void }) {
  const [templates, setTemplates] = useState<QCTemplate[]>([]);
  const [aktiv, setAktiv] = useState<QCTemplate | null>(null);
  const [eingaben, setEingaben] = useState<Record<string, unknown>>({});
  const [fehler, setFehler] = useState<string | null>(null);
  const [erzeugt, setErzeugt] = useState(false);
  const navigate = useNavigate();

  const maschinen = useAppStore((s) => s.maschinen);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const materialien = useAppStore((s) => s.materialien);

  const [maschineId, setMaschineId] = useState("");
  const [werkzeugId, setWerkzeugId] = useState("");
  const [materialId, setMaterialId] = useState("");

  useEffect(() => {
    void camwosaApi.quickcamTemplates().then(setTemplates).catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    if (!maschineId && maschinen[0]) setMaschineId(maschinen[0].id);
    if (!werkzeugId && werkzeuge[0]) setWerkzeugId(werkzeuge[0].id);
    if (!materialId && materialien[0]) setMaterialId(materialien[0].id);
  }, [maschinen, werkzeuge, materialien]);

  function waehleTemplate(t: QCTemplate) {
    const def: Record<string, unknown> = {};
    for (const p of t.parameter) def[p.name] = p.default;
    setEingaben(def);
    setAktiv(t);
    setErzeugt(false);
    setFehler(null);
  }

  async function erzeugen() {
    if (!aktiv) return;
    setFehler(null);
    try {
      const { projekt } = await camwosaApi.quickcamErzeugen(
        aktiv.id, eingaben, maschineId, werkzeugId, materialId,
        `QuickCAM: ${aktiv.name}`,
      );
      // #50: erzeugtes Projekt in die flachen Stores laden (sonst Dead-End)
      quickcamProjektInStores(projekt);
      setErzeugt(true);
      onErzeugt?.();
      navigate("/operationen");  // direkt zur Bearbeitung fuehren
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Erzeugen fehlgeschlagen");
    }
  }

  const passende_werkzeuge = useMemo(() => {
    if (!aktiv) return werkzeuge;
    // Tasche/Kontur/Bohren: kein V-Bit. Gravur: gerne V-Bit.
    if (aktiv.operation_typ === "gravur") return werkzeuge;
    return werkzeuge.filter((w) => w.typ !== "v_bit");
  }, [aktiv, werkzeuge]);

  return (
    <div className="space-y-6">
      <header>
        <CoachMark
          id="quickstart_intro"
          text='Vier Vorlagen unten: Klick auf eine, Maße eingeben, fertig. Wer mehr Kontrolle will, geht zu „Projekt".'
          ablauf_tage={30}
        >
          <h1 className="text-2xl font-bold">Schnellstart</h1>
        </CoachMark>
        <p className="text-sm text-camwosa-muted">
          Direkt loslegen — Vorlage waehlen, Maße eingeben, fertig. Wer mehr will,
          wechselt links zu „Projekt" und baut Operationen frei zusammen.
        </p>
      </header>

      {/* Template-Galerie — responsive: 1 Spalte auf 10", 2 auf Tablet, 4 auf 34" */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
        {templates.map((t) => (
          <button
            key={t.id}
            onClick={() => waehleTemplate(t)}
            className={[
              "flex flex-col items-start gap-2 rounded-lg border p-4 text-left transition",
              aktiv?.id === t.id
                ? "border-camwosa-accent bg-camwosa-accent/10"
                : "border-gray-700 bg-camwosa-surface hover:border-camwosa-accent/60",
            ].join(" ")}
          >
            <span className="text-3xl">{t.icon}</span>
            <span className="font-semibold">{t.name}</span>
            <span className="text-xs text-camwosa-muted">{t.kurzbeschreibung}</span>
          </button>
        ))}
      </div>

      {aktiv && (
        <section className="space-y-4 rounded-lg border border-gray-700 bg-camwosa-surface p-4">
          <h2 className="text-lg font-semibold">{aktiv.name} — Eingaben</h2>

          {/* Maschine / Werkzeug / Material */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Select label="Maschine" value={maschineId} onChange={setMaschineId}
              options={maschinen.map((m) => ({ value: m.id, label: m.name }))} />
            <Select label="Werkzeug" value={werkzeugId} onChange={setWerkzeugId}
              options={passende_werkzeuge.map((w) => ({
                value: w.id, label: `${w.name} (${w.durchmesser}mm)`,
              }))} />
            <Select label="Material" value={materialId} onChange={setMaterialId}
              options={materialien.map((m) => ({ value: m.id, label: m.name }))} />
          </div>

          {/* Template-spezifische Felder */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {aktiv.parameter.map((p) => (
              <ParamFeld
                key={p.name}
                p={p}
                value={eingaben[p.name]}
                onChange={(v) => setEingaben((prev) => ({ ...prev, [p.name]: v }))}
              />
            ))}
          </div>

          {fehler && (
            <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
              {fehler}
            </div>
          )}

          {erzeugt && (
            <div className="rounded border border-green-700 bg-green-900/30 p-2 text-sm text-green-300">
              Projekt erzeugt — wechsle zu „Projekt" / „Vorschau", um es zu sehen.
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              className="rounded bg-camwosa-accent px-4 py-2 font-medium text-camwosa-bg hover:opacity-90"
              onClick={() => void erzeugen()}
              disabled={!maschineId || !werkzeugId || !materialId}
            >
              Projekt erzeugen
            </button>
            <button
              className="rounded border border-gray-600 px-4 py-2 text-sm hover:bg-gray-700"
              onClick={() => setAktiv(null)}
            >
              Abbrechen
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

function Select({
  label, value, onChange, options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <label className="text-sm">
      <span className="mb-0.5 block text-xs text-camwosa-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      >
        <option value="">-- waehlen --</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

function ParamFeld({
  p, value, onChange,
}: {
  p: TemplateParameter;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const istZahl = p.typ === "float" || p.typ === "int";
  return (
    <label className="text-sm">
      <span className="mb-0.5 block text-xs text-camwosa-muted">
        {p.label} {p.einheit && <span>({p.einheit})</span>}
      </span>
      <input
        type={istZahl ? "number" : "text"}
        value={value as string | number ?? ""}
        step={p.typ === "int" ? 1 : 0.1}
        onChange={(e) => {
          const v = e.target.value;
          if (istZahl) onChange(v === "" ? "" : Number(v));
          else onChange(v);
        }}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
      {p.hinweis && (
        <span className="mt-0.5 block text-[10px] text-camwosa-muted">{p.hinweis}</span>
      )}
    </label>
  );
}
