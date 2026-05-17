import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import type { Material, MaterialKategorie } from "../api/types";
import { FachTooltip } from "../components/Tooltip";
import { FACHBEGRIFFE } from "../components/fachbegriffe";

const KAT_LABELS: Record<MaterialKategorie, string> = {
  holz: "Holz",
  holzwerkstoff: "Holzwerkstoff",
  kunststoff: "Kunststoff",
  ne_metall: "NE-Metall",
  metall: "Metall",
  sonstiges: "Sonstiges",
};

const LEER: Material = {
  id: "", name: "", kategorie: "holz",
  unter_kategorie: "",
  presets: [],
  spaeneabsaugung_empfohlen: false,
};

interface Props {
  initial?: Material | null;
  onGespeichert: (m: Material) => void;
  onAbbrechen: () => void;
}

export default function MaterialEditor({ initial, onGespeichert, onAbbrechen }: Props) {
  const [m, setM] = useState<Material>(initial ?? LEER);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => { setM(initial ?? LEER); }, [initial]);

  function update<K extends keyof Material>(feld: K, wert: Material[K]) {
    setM((prev) => ({ ...prev, [feld]: wert }));
  }

  async function speichern() {
    setFehler(null);
    try {
      if (initial) {
        const r = await camwosaApi.materialUpdaten(initial.id, m);
        onGespeichert(r.material);
      } else {
        const r = await camwosaApi.materialAnlegen(m);
        onGespeichert(r.material);
      }
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Speichern fehlgeschlagen");
    }
  }

  return (
    <div className="space-y-4 text-sm">
      <section>
        <h3 className="mb-2 font-semibold">Basisdaten</h3>
        <div className="grid grid-cols-2 gap-3">
          <Feld label="ID (eindeutig)">
            <input
              className="w-full rounded bg-camwosa-bg px-2 py-1 font-mono text-xs"
              value={m.id} disabled={!!initial}
              onChange={(e) => update("id", e.target.value)}
              placeholder="z.B. user_mdf_22"
            />
          </Feld>
          <Feld label="Name">
            <input
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.name}
              onChange={(e) => update("name", e.target.value)}
            />
          </Feld>
          <Feld label="Kategorie">
            <select
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.kategorie}
              onChange={(e) => update("kategorie", e.target.value as MaterialKategorie)}
            >
              {Object.entries(KAT_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </Feld>
          <Feld label="Unter-Kategorie">
            <input
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.unter_kategorie ?? ""}
              onChange={(e) => update("unter_kategorie", e.target.value)}
              placeholder="z.B. Hartholz, MDF, ABS"
            />
          </Feld>
        </div>
      </section>

      <section>
        <h3 className="mb-2 flex items-center font-semibold">
          Materialeigenschaften
          <FachTooltip {...FACHBEGRIFFE.schnittgeschwindigkeit} />
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <NumFeld label="Janka-Haerte (nur Holz)" v={m.janka_haerte ?? null}
            on={(n) => update("janka_haerte", n)} step={10} />
          <NumFeld label="Dichte (g/cm³)" v={m.dichte ?? null}
            on={(n) => update("dichte", n)} step={0.01} />
          <NumFeld label="Vc min (m/min)" v={m.schnittgeschwindigkeit_min ?? null}
            on={(n) => update("schnittgeschwindigkeit_min", n)} step={10} />
          <NumFeld label="Vc max (m/min)" v={m.schnittgeschwindigkeit_max ?? null}
            on={(n) => update("schnittgeschwindigkeit_max", n)} step={10} />
        </div>
        <label className="mt-3 flex items-center gap-2">
          <input
            type="checkbox"
            checked={m.spaeneabsaugung_empfohlen ?? false}
            onChange={(e) => update("spaeneabsaugung_empfohlen", e.target.checked)}
          />
          <span>Spaeneabsaugung empfohlen</span>
        </label>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Hinweise</h3>
        <div className="space-y-2">
          <textarea
            className="w-full rounded bg-camwosa-bg px-2 py-1"
            rows={2}
            value={m.risiken ?? ""}
            onChange={(e) => update("risiken", e.target.value)}
            placeholder="Risiken / Sicherheitshinweise"
          />
          <textarea
            className="w-full rounded bg-camwosa-bg px-2 py-1"
            rows={2}
            value={m.notizen ?? ""}
            onChange={(e) => update("notizen", e.target.value)}
            placeholder="Notizen, Quellen, Erfahrungen"
          />
        </div>
      </section>

      <p className="rounded bg-camwosa-bg p-2 text-xs text-camwosa-muted">
        💡 Schnittparameter (Presets) sind eigene CuttingPresets — siehe den
        Tab „Presets" im Material-Detail.
      </p>

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
          {fehler}
        </div>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <button
          className="rounded border border-gray-600 px-4 py-1 text-sm hover:bg-gray-700"
          onClick={onAbbrechen}
        >
          Abbrechen
        </button>
        <button
          className="rounded bg-camwosa-accent px-4 py-1 text-sm font-medium text-camwosa-bg hover:opacity-90"
          onClick={() => void speichern()}
        >
          {initial ? "Speichern" : "Anlegen"}
        </button>
      </div>
    </div>
  );
}

function Feld({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-0.5 block text-xs text-camwosa-muted">{label}</label>
      {children}
    </div>
  );
}

function NumFeld({
  label, v, on, step = 1,
}: {
  label: string;
  v: number | null;
  on: (n: number | null) => void;
  step?: number;
}) {
  return (
    <div>
      <label className="mb-0.5 block text-xs text-camwosa-muted">{label}</label>
      <input
        type="number"
        step={step}
        value={v ?? ""}
        onChange={(e) => {
          const s = e.target.value;
          on(s === "" ? null : Number(s));
        }}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
    </div>
  );
}
