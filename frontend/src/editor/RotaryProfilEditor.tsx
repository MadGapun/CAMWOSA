import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import type { RotaryProfil } from "../api/types";

interface Props {
  initial?: RotaryProfil | null;
  onGespeichert: (p: RotaryProfil) => void;
  onAbbrechen: () => void;
}

const LEER: RotaryProfil = {
  id: "", name: "", hersteller: "", modell: "",
  spannfutter_backen_anzahl: 3,
  spannfutter_max_durchmesser_mm: 80,
  spannfutter_min_durchmesser_mm: 5,
  hat_reitstock: false,
  reitstock_verstellbar_mm: null,
  max_werkstueck_laenge_mm: 300,
  durchschiebbar: true,
  grbl_y_steps_pro_grad: 88.889,
  grbl_y_limit_aufheben: true,
  cncjs_macro_ein: null,
  cncjs_macro_aus: null,
  notizen: "",
};

export default function RotaryProfilEditor({ initial, onGespeichert, onAbbrechen }: Props) {
  const [p, setP] = useState<RotaryProfil>(initial ?? LEER);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => { setP(initial ?? LEER); }, [initial]);

  function up<K extends keyof RotaryProfil>(feld: K, wert: RotaryProfil[K]) {
    setP((prev) => ({ ...prev, [feld]: wert }));
  }

  async function speichern() {
    setFehler(null);
    if (!p.id.trim()) { setFehler("Bitte eine eindeutige ID vergeben."); return; }
    if (p.spannfutter_max_durchmesser_mm < p.spannfutter_min_durchmesser_mm) {
      setFehler("Max-Durchmesser darf nicht kleiner als Min-Durchmesser sein."); return;
    }
    try {
      const r = initial
        ? await camwosaApi.rotaryProfilUpdaten(initial.id, p)
        : await camwosaApi.rotaryProfilAnlegen(p);
      onGespeichert(r.rotary_profil);
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
            <input className="w-full rounded bg-camwosa-bg px-2 py-1 font-mono text-xs"
              value={p.id} disabled={!!initial} onChange={(e) => up("id", e.target.value)}
              placeholder="z.B. user_4achs_chuck_65mm" />
          </Feld>
          <Feld label="Name">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={p.name} onChange={(e) => up("name", e.target.value)} />
          </Feld>
          <Feld label="Hersteller">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={p.hersteller} onChange={(e) => up("hersteller", e.target.value)} />
          </Feld>
          <Feld label="Modell">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={p.modell} onChange={(e) => up("modell", e.target.value)} />
          </Feld>
          <Feld label="Quelle-URL (optional)">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={p.quelle_url ?? ""} onChange={(e) => up("quelle_url", e.target.value || null)} />
          </Feld>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Spannfutter</h3>
        <div className="grid grid-cols-3 gap-3">
          <NumFeld label="Backen-Anzahl" v={p.spannfutter_backen_anzahl}
            on={(n) => up("spannfutter_backen_anzahl", Math.round(n ?? 0))} step={1} />
          <NumFeld label="Min-Ø (mm)" v={p.spannfutter_min_durchmesser_mm}
            on={(n) => up("spannfutter_min_durchmesser_mm", n ?? 0)} step={1} />
          <NumFeld label="Max-Ø (mm)" v={p.spannfutter_max_durchmesser_mm}
            on={(n) => up("spannfutter_max_durchmesser_mm", n ?? 0)} step={1} />
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Werkstück & Reitstock</h3>
        <div className="grid grid-cols-2 gap-3">
          <NumFeld label="Max. Werkstück-Länge (mm)" v={p.max_werkstueck_laenge_mm}
            on={(n) => up("max_werkstueck_laenge_mm", n ?? 0)} step={10} />
          <div className="flex items-end gap-4">
            <label className="flex items-center gap-2 text-xs">
              <input type="checkbox" checked={p.hat_reitstock}
                onChange={(e) => up("hat_reitstock", e.target.checked)} />
              Reitstock vorhanden
            </label>
            <label className="flex items-center gap-2 text-xs">
              <input type="checkbox" checked={p.durchschiebbar}
                onChange={(e) => up("durchschiebbar", e.target.checked)} />
              durchschiebbar
            </label>
          </div>
          {p.hat_reitstock && (
            <NumFeld label="Reitstock verstellbar (mm)" v={p.reitstock_verstellbar_mm ?? null}
              on={(n) => up("reitstock_verstellbar_mm", n)} step={10} />
          )}
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">GRBL (Y→A-Remap)</h3>
        <div className="grid grid-cols-2 gap-3">
          <NumFeld label="Y-Steps pro Grad ($101)" v={p.grbl_y_steps_pro_grad ?? null}
            on={(n) => up("grbl_y_steps_pro_grad", n)} step={0.001}
            hint="z.B. 88.889 für die ProVerXL-Rotary." />
          <label className="flex items-end gap-2 pb-1 text-xs">
            <input type="checkbox" checked={p.grbl_y_limit_aufheben}
              onChange={(e) => up("grbl_y_limit_aufheben", e.target.checked)} />
            Y-Soft-Limit aufheben ($130/Endless)
          </label>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">CNCjs-Macros (optional)</h3>
        <div className="grid grid-cols-2 gap-3">
          <Feld label="Macro „Rotary EIN“">
            <textarea className="w-full rounded bg-camwosa-bg px-2 py-1 font-mono text-xs" rows={3}
              value={p.cncjs_macro_ein ?? ""} onChange={(e) => up("cncjs_macro_ein", e.target.value || null)} />
          </Feld>
          <Feld label="Macro „Rotary AUS“">
            <textarea className="w-full rounded bg-camwosa-bg px-2 py-1 font-mono text-xs" rows={3}
              value={p.cncjs_macro_aus ?? ""} onChange={(e) => up("cncjs_macro_aus", e.target.value || null)} />
          </Feld>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Notizen</h3>
        <textarea className="w-full rounded bg-camwosa-bg px-2 py-1" rows={2}
          value={p.notizen ?? ""} onChange={(e) => up("notizen", e.target.value)} />
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
  label, v, on, step = 1, hint,
}: { label: string; v: number | null; on: (n: number | null) => void; step?: number; hint?: string }) {
  return (
    <div>
      <label className="mb-0.5 block text-xs text-camwosa-muted">{label}</label>
      <input type="number" step={step} value={v ?? ""}
        onChange={(e) => { const x = e.target.value; on(x === "" ? null : Number(x)); }}
        className="w-full rounded bg-camwosa-bg px-2 py-1" />
      {hint && <p className="mt-0.5 text-[10px] text-camwosa-muted">{hint}</p>}
    </div>
  );
}
