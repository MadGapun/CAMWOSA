import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import type { Spindel, SpindelTyp, SpindelHerkunft } from "../api/types";

const TYP_OPTIONEN: { value: SpindelTyp; label: string }[] = [
  { value: "manuell", label: "Manuell (Router, Drehzahl am Rad)" },
  { value: "PWM", label: "PWM (GRBL S-Wert / VFD über 0–10 V)" },
  { value: "analog", label: "Analog (0–10 V direkt)" },
];

const HERKUNFT_OPTIONEN: { value: SpindelHerkunft; label: string }[] = [
  { value: "oem", label: "OEM (Original)" },
  { value: "upgrade", label: "Upgrade (nachgerüstet)" },
  { value: "eigenbau", label: "Eigenbau" },
];

interface Props {
  initial?: Spindel | null;
  onGespeichert: (s: Spindel) => void;
  onAbbrechen: () => void;
}

const LEER: Spindel = {
  id: "",
  name: "",
  hersteller: "",
  modell: "",
  typ: "PWM",
  rpm_min: 6000,
  rpm_max: 24000,
  leistung_watt: 1500,
  kuehlung: "luft",
  rampen_zeit_s: 3.0,
  herkunft: "upgrade",
};

export default function SpindelEditor({ initial, onGespeichert, onAbbrechen }: Props) {
  const [s, setS] = useState<Spindel>(initial ?? LEER);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => { setS(initial ?? LEER); }, [initial]);

  function up<K extends keyof Spindel>(feld: K, wert: Spindel[K]) {
    setS((prev) => ({ ...prev, [feld]: wert }));
  }

  const istGesteuert = s.typ === "PWM" || s.typ === "analog";

  async function speichern() {
    setFehler(null);
    if (!s.id.trim()) { setFehler("Bitte eine eindeutige ID vergeben."); return; }
    if (s.rpm_max < s.rpm_min) { setFehler("Max-Drehzahl muss ≥ Min-Drehzahl sein."); return; }
    try {
      const r = initial
        ? await camwosaApi.spindelUpdaten(initial.id, s)
        : await camwosaApi.spindelAnlegen(s);
      onGespeichert(r.spindel);
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
              value={s.id} disabled={!!initial}
              onChange={(e) => up("id", e.target.value)}
              placeholder="z.B. spindle_1500w_aircooled_vfd"
            />
          </Feld>
          <Feld label="Name (Anzeige)">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={s.name} onChange={(e) => up("name", e.target.value)}
              placeholder="z.B. 1,5 kW Spindel (luftgekühlt, VFD)" />
          </Feld>
          <Feld label="Hersteller">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={s.hersteller} onChange={(e) => up("hersteller", e.target.value)} />
          </Feld>
          <Feld label="Modell">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={s.modell} onChange={(e) => up("modell", e.target.value)} />
          </Feld>
          <Feld label="Steuerungs-Typ">
            <select className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={s.typ} onChange={(e) => up("typ", e.target.value as SpindelTyp)}>
              {TYP_OPTIONEN.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </Feld>
          <Feld label="Herkunft">
            <select className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={s.herkunft} onChange={(e) => up("herkunft", e.target.value as SpindelHerkunft)}>
              {HERKUNFT_OPTIONEN.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </Feld>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Drehzahl & Leistung</h3>
        <div className="grid grid-cols-2 gap-3">
          <NumFeld label="Min-Drehzahl (min⁻¹)" v={s.rpm_min} on={(n) => up("rpm_min", n ?? 0)} step={500}
            hint="Nutzbare Untergrenze (VFD-Spindeln haben unten wenig Drehmoment)." />
          <NumFeld label="Max-Drehzahl (min⁻¹)" v={s.rpm_max} on={(n) => up("rpm_max", n ?? 0)} step={500}
            hint="Oberer S-Wert. Sollte zu GRBL $30 passen." />
          <NumFeld label="Leistung (W)" v={s.leistung_watt ?? null} on={(n) => up("leistung_watt", n)} step={50} />
          <NumFeld label="Drehmoment (Ncm)" v={s.drehmoment_ncm ?? null} on={(n) => up("drehmoment_ncm", n)} step={5} />
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Mechanik & Hochlauf</h3>
        <div className="grid grid-cols-2 gap-3">
          <NumFeld label="Spannzangen-Ø / Schaft (mm)" v={s.schaft_durchmesser_mm ?? null}
            on={(n) => up("schaft_durchmesser_mm", n)} step={0.05}
            hint="ER11 ≈ bis 7 mm · ER16 ≈ bis 10 mm · ER20 ≈ bis 13 mm" />
          <Feld label="Kühlung">
            <select className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={s.kuehlung} onChange={(e) => up("kuehlung", e.target.value)}>
              <option value="luft">Luft</option>
              <option value="wasser">Wasser</option>
              <option value="sonstige">Sonstige</option>
            </select>
          </Feld>
          <NumFeld label="Hochlauf-Dwell (s)" v={s.rampen_zeit_s ?? null} on={(n) => up("rampen_zeit_s", n)} step={0.5}
            hint="G4-Pause nach M3, bis die Spindel auf Drehzahl ist (VFD-Accel). NICHT der manuelle Warmlauf." />
          <NumFeld label="Warmlauf-Zeit (s)" v={s.warmlauf_zeit_s ?? null} on={(n) => up("warmlauf_zeit_s", n)} step={1} min={0}
            hint="Optionaler Spindel-Warmlauf am Programmstart (schont VFD/Lager). 0/leer = aus." />
          <NumFeld label="Warmlauf-Drehzahl (U/min)" v={s.warmlauf_rpm ?? null} on={(n) => up("warmlauf_rpm", n)} step={500} min={0}
            hint="Moderate Drehzahl während des Warmlaufs, z.B. 8000. Nur mit Warmlauf-Zeit." />
          <NumFeld label="Gewicht (g)" v={s.gewicht_g ?? null} on={(n) => up("gewicht_g", n)} step={50} />
        </div>
      </section>

      {istGesteuert && (
        <section className="rounded border border-blue-700/40 bg-blue-900/10 p-3">
          <h3 className="mb-2 font-semibold">PWM-Kennlinie (optional)</h3>
          <div className="grid grid-cols-2 gap-3">
            <NumFeld label="PWM bei Min-Drehzahl (‰)" v={s.pwm_min_promille ?? null}
              on={(n) => up("pwm_min_promille", n)} step={10} min={0} max={1000} />
            <NumFeld label="PWM bei Max-Drehzahl (‰)" v={s.pwm_max_promille ?? null}
              on={(n) => up("pwm_max_promille", n)} step={10} min={0} max={1000} />
          </div>
          <p className="mt-1 text-[10px] text-camwosa-muted">
            Nur nötig, wenn GRBL den S-Wert nicht direkt als Drehzahl ausgibt.
          </p>
        </section>
      )}

      <section>
        <h3 className="mb-2 font-semibold">Notizen</h3>
        <textarea className="w-full rounded bg-camwosa-bg px-2 py-1" rows={3}
          value={s.notizen ?? ""} onChange={(e) => up("notizen", e.target.value)}
          placeholder="z.B. VFD-Parameter, Warmlauf-Routine, Besonderheiten" />
      </section>

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">{fehler}</div>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <button className="rounded border border-gray-600 px-4 py-1 text-sm hover:bg-gray-700"
          onClick={onAbbrechen}>Abbrechen</button>
        <button className="rounded bg-camwosa-accent px-4 py-1 text-sm font-medium text-camwosa-bg hover:opacity-90"
          onClick={() => void speichern()}>{initial ? "Speichern" : "Anlegen"}</button>
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
  label, v, on, step = 1, min, max, hint,
}: {
  label: string; v: number | null; on: (n: number | null) => void;
  step?: number; min?: number; max?: number; hint?: string;
}) {
  return (
    <div>
      <label className="mb-0.5 block text-xs text-camwosa-muted">{label}</label>
      <input type="number" step={step} min={min} max={max} value={v ?? ""}
        onChange={(e) => { const x = e.target.value; on(x === "" ? null : Number(x)); }}
        className="w-full rounded bg-camwosa-bg px-2 py-1" />
      {hint && <p className="mt-0.5 text-[10px] text-camwosa-muted">{hint}</p>}
    </div>
  );
}
