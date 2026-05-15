import { useState } from "react";
import { useTranslation } from "react-i18next";
import { camwosaApi } from "../api/client";

interface NestingResult {
  platzierungen: Array<{
    teil_id: string;
    instanz_index: number;
    x: number;
    y: number;
    breite: number;
    hoehe: number;
    rotation_grad: number;
  }>;
  verschnitt_prozent: number;
  nicht_platziert: Array<{ teil_id: string; instanz_index: number }>;
}

export default function NestingView() {
  const { t } = useTranslation();
  const [teil, setTeil] = useState({ breite: 130, hoehe: 130, anzahl: 4 });
  const [platte, setPlatte] = useState({ breite: 600, hoehe: 400 });
  const [result, setResult] = useState<NestingResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    try {
      const r = await camwosaApi.nestingRun(
        [{ id: "teil", ...teil }],
        [{ id: "platte", ...platte }],
      );
      setResult(r as NestingResult);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.nesting")}</h1>

      <section className="grid grid-cols-2 gap-4">
        <div className="rounded border border-gray-700 bg-camwosa-surface p-4">
          <h2 className="mb-2 font-semibold">Teil</h2>
          <label className="block text-xs">Breite (mm)</label>
          <input type="number" className="mb-2 w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
                 value={teil.breite}
                 onChange={(e) => setTeil({ ...teil, breite: +e.target.value })} />
          <label className="block text-xs">Hoehe (mm)</label>
          <input type="number" className="mb-2 w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
                 value={teil.hoehe}
                 onChange={(e) => setTeil({ ...teil, hoehe: +e.target.value })} />
          <label className="block text-xs">Anzahl</label>
          <input type="number" className="w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
                 value={teil.anzahl}
                 onChange={(e) => setTeil({ ...teil, anzahl: +e.target.value })} />
        </div>
        <div className="rounded border border-gray-700 bg-camwosa-surface p-4">
          <h2 className="mb-2 font-semibold">Platte</h2>
          <label className="block text-xs">Breite (mm)</label>
          <input type="number" className="mb-2 w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
                 value={platte.breite}
                 onChange={(e) => setPlatte({ ...platte, breite: +e.target.value })} />
          <label className="block text-xs">Hoehe (mm)</label>
          <input type="number" className="w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
                 value={platte.hoehe}
                 onChange={(e) => setPlatte({ ...platte, hoehe: +e.target.value })} />
        </div>
      </section>

      <button
        className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        onClick={() => void run()}
        disabled={loading}
      >
        {loading ? "Lade..." : t("nesting.starten")}
      </button>

      {result && (
        <div className="rounded border border-gray-700 bg-camwosa-surface p-4 text-sm">
          <p>
            <strong>{t("nesting.verschnitt")}:</strong>{" "}
            {result.verschnitt_prozent.toFixed(1)}%
          </p>
          <p>Platziert: {result.platzierungen.length}</p>
          <p>Nicht platziert: {result.nicht_platziert.length}</p>
        </div>
      )}
    </div>
  );
}
