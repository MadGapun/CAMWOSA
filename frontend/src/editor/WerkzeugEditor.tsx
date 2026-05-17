import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import type { Werkzeug, WerkzeugTyp } from "../api/types";
import { CoachMark } from "../components/Tooltip";

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

interface Props {
  initial?: Werkzeug | null;
  onGespeichert: (w: Werkzeug) => void;
  onAbbrechen: () => void;
}

const LEER: Werkzeug = {
  id: "",
  name: "",
  typ: "schaftfraeser",
  durchmesser: 6,
  schaft_durchmesser: 6,
  schneidlaenge: 22,
  gesamtlaenge: 50,
  schneiden: 2,
};

export default function WerkzeugEditor({ initial, onGespeichert, onAbbrechen }: Props) {
  const [w, setW] = useState<Werkzeug>(initial ?? LEER);
  const [fehler, setFehler] = useState<string | null>(null);
  const [helperBusy, setHelperBusy] = useState(false);

  useEffect(() => {
    setW(initial ?? LEER);
  }, [initial]);

  function update<K extends keyof Werkzeug>(feld: K, wert: Werkzeug[K]) {
    setW((prev) => ({ ...prev, [feld]: wert }));
  }

  async function helperWinkelAusSpitze() {
    if (
      w.spitzendurchmesser == null
      || w.durchmesser <= w.spitzendurchmesser
      || w.schneidlaenge <= 0
    ) {
      setFehler("Spitzendurchmesser, Schneid-Durchmesser und Schneidlaenge muessen sinnvoll sein");
      return;
    }
    setHelperBusy(true);
    try {
      const r = await camwosaApi.vBitWinkel(
        w.spitzendurchmesser, w.durchmesser, w.schneidlaenge,
      );
      update("spitzenwinkel", Math.round(r.spitzenwinkel_grad * 10) / 10);
      setFehler(null);
    } catch (e: any) {
      setFehler(e.message ?? "Helper-Fehler");
    } finally {
      setHelperBusy(false);
    }
  }

  async function helperSpitzeAusWinkel() {
    if (w.spitzenwinkel == null || w.schneidlaenge <= 0 || w.durchmesser <= 0) {
      setFehler("Spitzenwinkel, Schneidlaenge und Durchmesser muessen sinnvoll sein");
      return;
    }
    setHelperBusy(true);
    try {
      const r = await camwosaApi.vBitSpitze(
        w.spitzenwinkel, w.schneidlaenge, w.durchmesser,
      );
      update("spitzendurchmesser", Math.max(0, Math.round(r.spitzendurchmesser_mm * 100) / 100));
      setFehler(null);
    } catch (e: any) {
      setFehler(e.message ?? "Helper-Fehler");
    } finally {
      setHelperBusy(false);
    }
  }

  async function speichern() {
    setFehler(null);
    try {
      if (initial) {
        const r = await camwosaApi.werkzeugUpdaten(initial.id, w);
        onGespeichert(r.werkzeug);
      } else {
        const r = await camwosaApi.werkzeugAnlegen(w);
        onGespeichert(r.werkzeug);
      }
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Speichern fehlgeschlagen");
    }
  }

  const istKonisch = w.typ === "v_bit" || w.typ === "gravierstichel";

  return (
    <div className="space-y-4 text-sm">
      <section>
        <h3 className="mb-2 font-semibold">Basisdaten</h3>
        <div className="grid grid-cols-2 gap-3">
          <Feld label="ID (eindeutig)" htmlFor="id">
            <input
              id="id"
              className="w-full rounded bg-camwosa-bg px-2 py-1 font-mono text-xs"
              value={w.id}
              disabled={!!initial}
              onChange={(e) => update("id", e.target.value)}
              placeholder="z.B. user_gravurstichel_03"
            />
          </Feld>
          <Feld label="Name (Anzeige)" htmlFor="name">
            <input
              id="name"
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={w.name}
              onChange={(e) => update("name", e.target.value)}
            />
          </Feld>
          <Feld label="Typ" htmlFor="typ">
            <select
              id="typ"
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={w.typ}
              onChange={(e) => update("typ", e.target.value as WerkzeugTyp)}
            >
              {Object.entries(TYP_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </Feld>
          <Feld label="Schneiden" htmlFor="schneiden">
            <input
              id="schneiden" type="number" min={1} max={12}
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={w.schneiden}
              onChange={(e) => update("schneiden", Number(e.target.value))}
            />
          </Feld>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Geometrie</h3>
        <div className="grid grid-cols-2 gap-3">
          <NumFeld label="Schneid-Ø (mm)" v={w.durchmesser}
            on={(n) => update("durchmesser", n)} step={0.1} />
          <NumFeld label="Schaft-Ø (mm)" v={w.schaft_durchmesser}
            on={(n) => update("schaft_durchmesser", n)} step={0.1} />
          <NumFeld label="Schneidlaenge (mm)" v={w.schneidlaenge}
            on={(n) => update("schneidlaenge", n)} step={0.5} />
          <NumFeld label="Gesamtlaenge (mm)" v={w.gesamtlaenge}
            on={(n) => update("gesamtlaenge", n)} step={0.5} />
          <NumFeld label="Max. Arbeitstiefe (mm)"
            v={w.max_arbeitstiefe_mm ?? null}
            on={(n) => update("max_arbeitstiefe_mm", n)}
            step={0.5}
            hint="Leer = Schneidlaenge. Schaft taucht nie tiefer ein."
          />
        </div>
      </section>

      {(istKonisch || w.spitzenwinkel != null || w.spitzendurchmesser != null) && (
        <section className="rounded border border-blue-700/40 bg-blue-900/10 p-3">
          <h3 className="mb-2 font-semibold">
            Konische Werkzeuge (V-Bit / Gravurstichel)
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <NumFeld label="Spitzenwinkel (°)" v={w.spitzenwinkel ?? null}
              on={(n) => update("spitzenwinkel", n)} step={1} min={10} max={180} />
            <NumFeld label="Spitzendurchmesser (mm)" v={w.spitzendurchmesser ?? null}
              on={(n) => update("spitzendurchmesser", n)} step={0.01}
              hint="Bei V-Bit oft 0, bei Gravurstichel meist 0.1-0.3 mm"
            />
          </div>
          <CoachMark
            id="werkzeug_v_bit_helper"
            text="Bei Gravurstichel kennst du oft nur 2 der 3 Werte (Winkel / Spitzendurchmesser / Schneidlaenge). Die Buttons rechnen den fehlenden aus den anderen aus."
          >
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={helperBusy}
                onClick={() => void helperWinkelAusSpitze()}
                className="rounded border border-blue-600 px-3 py-1 text-xs hover:bg-blue-800/30 disabled:opacity-50"
              >
                ↻ Winkel aus Spitze + Schneidlaenge berechnen
              </button>
              <button
                type="button"
                disabled={helperBusy}
                onClick={() => void helperSpitzeAusWinkel()}
                className="rounded border border-blue-600 px-3 py-1 text-xs hover:bg-blue-800/30 disabled:opacity-50"
              >
                ↻ Spitze aus Winkel + Schneidlaenge berechnen
              </button>
            </div>
          </CoachMark>
        </section>
      )}

      <section>
        <h3 className="mb-2 font-semibold">Standzeit</h3>
        <NumFeld label="Standzeit max. (Minuten Schnitt)"
          v={w.standzeit_max_minuten ?? null}
          on={(n) => update("standzeit_max_minuten", n)} step={5}
          hint="Erfahrungswert. Wird vom Standzeit-Tracking benutzt."
        />
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Notizen</h3>
        <textarea
          className="w-full rounded bg-camwosa-bg px-2 py-1"
          rows={3}
          value={w.notizen ?? ""}
          onChange={(e) => update("notizen", e.target.value)}
          placeholder="z.B. Hersteller-Datenblatt-Link, Erfahrungswerte"
        />
      </section>

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

function Feld({
  label, htmlFor, children,
}: { label: string; htmlFor?: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-0.5 block text-xs text-camwosa-muted">
        {label}
      </label>
      {children}
    </div>
  );
}

function NumFeld({
  label, v, on, step = 1, min, max, hint,
}: {
  label: string;
  v: number | null;
  on: (n: number | null) => void;
  step?: number;
  min?: number;
  max?: number;
  hint?: string;
}) {
  return (
    <div>
      <label className="mb-0.5 block text-xs text-camwosa-muted">{label}</label>
      <input
        type="number"
        step={step}
        min={min}
        max={max}
        value={v ?? ""}
        onChange={(e) => {
          const s = e.target.value;
          on(s === "" ? null : Number(s));
        }}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
      {hint && <p className="mt-0.5 text-[10px] text-camwosa-muted">{hint}</p>}
    </div>
  );
}
