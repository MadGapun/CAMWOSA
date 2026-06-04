import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import type {
  ControllerTyp, MaschinenModus, MaschinenProfil, PostprozessorInfo,
} from "../api/types";

const CONTROLLER: ControllerTyp[] = ["GRBL", "Marlin", "LinuxCNC", "Mach3", "Duet", "Sonstige"];
const MODI: { value: MaschinenModus; label: string }[] = [
  { value: "standard_xyz", label: "Standard XYZ" },
  { value: "rotary_y", label: "Rotary (Y→A)" },
  { value: "rotary_x", label: "Rotary (X→A)" },
  { value: "laser", label: "Laser" },
  { value: "drag_knife", label: "Schleppmesser" },
];

interface Props {
  initial?: MaschinenProfil | null;
  onGespeichert: (m: MaschinenProfil) => void;
  onAbbrechen: () => void;
}

const LEER = {
  id: "", name: "", hersteller: "", modell: "", controller: "GRBL",
  arbeitsraum: { x: 300, y: 300, z: 100 },
  max_vorschub: 3000, sicherer_vorschub: 2000, eilgang: 5000,
  spindel_ids: [], aktive_spindel_id: null,
  spindel_typ: "PWM", spindel_rpm_min: 6000, spindel_rpm_max: 24000,
  sicherheitshoehe: 5.0, werkzeugwechsel_position: null,
  postprozessor: "grbl_standard",
  modi: ["standard_xyz"], aktiver_modus: "standard_xyz",
  notizen: "",
} as unknown as MaschinenProfil;

export default function MaschinenEditor({ initial, onGespeichert, onAbbrechen }: Props) {
  const spindeln = useAppStore((s) => s.spindeln);
  const [m, setM] = useState<MaschinenProfil>(initial ?? LEER);
  const [posts, setPosts] = useState<PostprozessorInfo[]>([]);
  const [fehler, setFehler] = useState<string | null>(null);
  const [erweitert, setErweitert] = useState(false);

  useEffect(() => { setM(initial ?? LEER); }, [initial]);
  useEffect(() => { camwosaApi.postprozessoren().then(setPosts).catch(() => setPosts([])); }, []);

  function up<K extends keyof MaschinenProfil>(feld: K, wert: MaschinenProfil[K]) {
    setM((prev) => ({ ...prev, [feld]: wert }));
  }
  function upRaum(achse: "x" | "y" | "z", wert: number) {
    setM((prev) => ({ ...prev, arbeitsraum: { ...prev.arbeitsraum, [achse]: wert } }));
  }

  const wwPos = m.werkzeugwechsel_position;
  function setWwAktiv(an: boolean) {
    up("werkzeugwechsel_position", an ? [0, 0, m.arbeitsraum.z] : null);
  }
  function setWw(i: number, wert: number) {
    const p: [number, number, number] = wwPos ? [...wwPos] : [0, 0, 0];
    p[i] = wert;
    up("werkzeugwechsel_position", p);
  }

  function toggleSpindel(id: string) {
    const drin = m.spindel_ids.includes(id);
    const neu = drin ? m.spindel_ids.filter((x) => x !== id) : [...m.spindel_ids, id];
    setM((prev) => ({
      ...prev,
      spindel_ids: neu,
      aktive_spindel_id: neu.includes(prev.aktive_spindel_id ?? "")
        ? prev.aktive_spindel_id : (neu[0] ?? null),
    }));
  }
  function toggleModus(val: MaschinenModus) {
    const drin = m.modi.includes(val);
    const neu = drin ? m.modi.filter((x) => x !== val) : [...m.modi, val];
    if (neu.length === 0) return; // mind. ein Modus
    setM((prev) => ({
      ...prev, modi: neu,
      aktiver_modus: neu.includes(prev.aktiver_modus) ? prev.aktiver_modus : neu[0],
    }));
  }

  async function speichern() {
    setFehler(null);
    if (!m.id.trim()) { setFehler("Bitte eine eindeutige ID vergeben."); return; }
    if (m.sicherer_vorschub > m.max_vorschub) {
      setFehler("Sicherer Vorschub darf nicht größer als Max-Vorschub sein."); return;
    }
    // Server-Anreicherung (_-Felder) vor dem Speichern entfernen, Rest mitnehmen.
    const payload: Record<string, unknown> = { ...m };
    Object.keys(payload).forEach((k) => { if (k.startsWith("_")) delete payload[k]; });
    try {
      const r = initial
        ? await camwosaApi.maschineUpdaten(initial.id, payload as unknown as MaschinenProfil)
        : await camwosaApi.maschineAnlegen(payload as unknown as MaschinenProfil);
      onGespeichert(r.maschine);
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
              value={m.id} disabled={!!initial} onChange={(e) => up("id", e.target.value)}
              placeholder="z.B. genmitsu_proverxl_4030_v2" />
          </Feld>
          <Feld label="Name">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.name} onChange={(e) => up("name", e.target.value)} />
          </Feld>
          <Feld label="Hersteller">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.hersteller} onChange={(e) => up("hersteller", e.target.value)} />
          </Feld>
          <Feld label="Modell">
            <input className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.modell} onChange={(e) => up("modell", e.target.value)} />
          </Feld>
          <Feld label="Controller">
            <select className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.controller} onChange={(e) => up("controller", e.target.value as ControllerTyp)}>
              {CONTROLLER.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Feld>
          <Feld label="Postprozessor">
            <select className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={m.postprozessor} onChange={(e) => up("postprozessor", e.target.value)}>
              {posts.length === 0 && <option value={m.postprozessor}>{m.postprozessor}</option>}
              {posts.map((p) => <option key={p.id} value={p.id}>{p.name ?? p.id}</option>)}
            </select>
          </Feld>
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Arbeitsraum (mm)</h3>
        <div className="grid grid-cols-3 gap-3">
          <NumFeld label="X" v={m.arbeitsraum.x} on={(n) => upRaum("x", n ?? 0)} step={10} />
          <NumFeld label="Y" v={m.arbeitsraum.y} on={(n) => upRaum("y", n ?? 0)} step={10} />
          <NumFeld label="Z" v={m.arbeitsraum.z} on={(n) => upRaum("z", n ?? 0)} step={10} />
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Geschwindigkeiten (mm/min) & Sicherheit</h3>
        <div className="grid grid-cols-3 gap-3">
          <NumFeld label="Max-Vorschub" v={m.max_vorschub} on={(n) => up("max_vorschub", n ?? 0)} step={100} />
          <NumFeld label="Sicherer Vorschub" v={m.sicherer_vorschub} on={(n) => up("sicherer_vorschub", n ?? 0)} step={100} />
          <NumFeld label="Eilgang (G0)" v={m.eilgang} on={(n) => up("eilgang", n ?? 0)} step={100} />
          <NumFeld label="Sicherheitshöhe (mm)" v={m.sicherheitshoehe} on={(n) => up("sicherheitshoehe", n ?? 0)} step={0.5} />
        </div>
        <div className="mt-2">
          <label className="flex items-center gap-2 text-xs">
            <input type="checkbox" checked={!!wwPos} onChange={(e) => setWwAktiv(e.target.checked)} />
            Werkzeugwechsel-Park-Position definieren
          </label>
          {wwPos && (
            <div className="mt-1 grid grid-cols-3 gap-3">
              <NumFeld label="WW X" v={wwPos[0]} on={(n) => setWw(0, n ?? 0)} step={10} />
              <NumFeld label="WW Y" v={wwPos[1]} on={(n) => setWw(1, n ?? 0)} step={10} />
              <NumFeld label="WW Z" v={wwPos[2]} on={(n) => setWw(2, n ?? 0)} step={10} />
            </div>
          )}
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Spindeln</h3>
        <div className="space-y-1">
          {spindeln.map((sp) => (
            <label key={sp.id} className="flex items-center justify-between gap-2 rounded bg-camwosa-bg px-2 py-1 text-xs">
              <span className="flex items-center gap-2">
                <input type="checkbox" checked={m.spindel_ids.includes(sp.id)}
                  onChange={() => toggleSpindel(sp.id)} />
                {sp.name}
                <span className="text-[10px] text-camwosa-muted">{sp.rpm_min}–{sp.rpm_max}</span>
              </span>
              {m.spindel_ids.includes(sp.id) && (
                <label className="flex items-center gap-1 text-[10px]">
                  <input type="radio" name="aktive_spindel"
                    checked={m.aktive_spindel_id === sp.id}
                    onChange={() => up("aktive_spindel_id", sp.id)} />
                  aktiv
                </label>
              )}
            </label>
          ))}
          {spindeln.length === 0 && (
            <p className="text-xs text-camwosa-muted">Keine Spindeln in der Bibliothek — erst eine anlegen.</p>
          )}
        </div>
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Modi</h3>
        <div className="flex flex-wrap gap-3">
          {MODI.map((mo) => (
            <label key={mo.value} className="flex items-center gap-1.5 text-xs">
              <input type="checkbox" checked={m.modi.includes(mo.value)}
                onChange={() => toggleModus(mo.value)} />
              {mo.label}
              {m.modi.includes(mo.value) && (
                <input type="radio" name="aktiver_modus" title="aktiver Modus"
                  checked={m.aktiver_modus === mo.value}
                  onChange={() => up("aktiver_modus", mo.value)} />
              )}
            </label>
          ))}
        </div>
        <p className="mt-1 text-[10px] text-camwosa-muted">Häkchen = verfügbar · Radio = aktiver Modus.</p>
      </section>

      <section>
        <button className="text-xs text-camwosa-accent" onClick={() => setErweitert((v) => !v)}>
          {erweitert ? "▾" : "▸"} Erweitert (Inline-RPM-Fallback)
        </button>
        {erweitert && (
          <div className="mt-2 grid grid-cols-3 gap-3">
            <Feld label="Spindel-Typ (Fallback)">
              <select className="w-full rounded bg-camwosa-bg px-2 py-1"
                value={m.spindel_typ} onChange={(e) => up("spindel_typ", e.target.value as any)}>
                <option value="manuell">manuell</option>
                <option value="PWM">PWM</option>
                <option value="analog">analog</option>
              </select>
            </Feld>
            <NumFeld label="RPM min (Fallback)" v={m.spindel_rpm_min} on={(n) => up("spindel_rpm_min", n ?? 0)} step={500} />
            <NumFeld label="RPM max (Fallback)" v={m.spindel_rpm_max} on={(n) => up("spindel_rpm_max", n ?? 0)} step={500} />
            <p className="col-span-3 text-[10px] text-camwosa-muted">
              Nur genutzt, wenn keine aktive Spindel zugeordnet ist.
            </p>
          </div>
        )}
      </section>

      <section>
        <h3 className="mb-2 font-semibold">Notizen</h3>
        <textarea className="w-full rounded bg-camwosa-bg px-2 py-1" rows={2}
          value={m.notizen ?? ""} onChange={(e) => up("notizen", e.target.value)} />
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
  label, v, on, step = 1,
}: { label: string; v: number | null; on: (n: number | null) => void; step?: number }) {
  return (
    <div>
      <label className="mb-0.5 block text-xs text-camwosa-muted">{label}</label>
      <input type="number" step={step} value={v ?? ""}
        onChange={(e) => { const x = e.target.value; on(x === "" ? null : Number(x)); }}
        className="w-full rounded bg-camwosa-bg px-2 py-1" />
    </div>
  );
}
