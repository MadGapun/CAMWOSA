import { useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import DrechselProfilEditor, { type ProfilPunkt } from "../editor/DrechselProfilEditor";
import type { DrechselParameter, DrechselStrategie, Toolpath } from "../api/types";
import { FachTooltip } from "../components/Tooltip";
import { FACHBEGRIFFE } from "../components/fachbegriffe";

const STRATEGIE_LABEL: Record<DrechselStrategie, string> = {
  laengs_schruppen: "Schruppen (parallele Schalen)",
  profil_schlichten: "Schlichten (folgt Profil)",
  schrupp_und_schlicht: "Schrupp + Schlicht (Default)",
  helix: "Helix (Schraubmuster / Nut)",
};

const VASE_DEFAULT: ProfilPunkt[] = [
  [0, 22], [10, 25], [40, 18], [80, 28], [110, 25], [120, 20],
];

/**
 * Drechseln-Spezial-View: Profil zeichnen + Parameter setzen + Toolpath erzeugen.
 *
 * Nutzt den Profil-Editor mit 2D-Halbschnitt + 3D-Revolution-Preview.
 * G-Code-Erzeugung geht direkt an den Backend-Endpoint und legt das Ergebnis
 * im App-Store als Operation ab.
 */
export default function DrechselnView() {
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const operationHinzufuegen = useAppStore((s) => s.operationHinzufuegen);

  const [profil, setProfil] = useState<ProfilPunkt[]>(VASE_DEFAULT);
  const [werkzeugId, setWerkzeugId] = useState(werkzeuge[0]?.id ?? "");
  const [strategie, setStrategie] = useState<DrechselStrategie>("schrupp_und_schlicht");
  const [rohRadius, setRohRadius] = useState(30);
  const [stepdown, setStepdown] = useState(1.5);
  const [aufmass, setAufmass] = useState(0.3);
  const [schlichtZustellung, setSchlichtZustellung] = useState(0.5);
  const [drehzahl, setDrehzahl] = useState(250);
  const [spindelRpm, setSpindelRpm] = useState(10000);
  const [vorschub, setVorschub] = useState(300);
  const [eintauchVorschub, setEintauchVorschub] = useState(150);

  // Helix-Felder
  const [helixSteigung, setHelixSteigung] = useState(2.0);
  const [helixTiefe, setHelixTiefe] = useState(2.0);
  const [helixPasses, setHelixPasses] = useState(1);

  const [erzeugt, setErzeugt] = useState<Toolpath | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const istHelix = strategie === "helix";
  const helixSyncFeed = istHelix ? helixSteigung * drehzahl : null;

  async function erzeugen() {
    if (!werkzeugId) { setFehler("Werkzeug waehlen"); return; }
    if (profil.length < 2) { setFehler("Mindestens 2 Profil-Punkte noetig"); return; }
    setBusy(true); setFehler(null);
    try {
      const max_tiefe = rohRadius - Math.min(...profil.map((p) => p[1]));
      const parameter: DrechselParameter = {
        werkzeug_id: werkzeugId,
        spindel_rpm: spindelRpm,
        vorschub, eintauch_vorschub: eintauchVorschub,
        sicherheitshoehe: 5,
        max_tiefe: Math.max(max_tiefe, 0.5),
        stepdown,
        strategie,
        rohmaterial_radius_mm: rohRadius,
        aufmass_schlichten_mm: aufmass,
        schlicht_zustellung_mm: schlichtZustellung,
        drehzahl_werkstueck_upm: drehzahl,
        profil,
        helix_steigung_mm_pro_umdrehung: helixSteigung,
        helix_tiefe_mm: helixTiefe,
        helix_anzahl_passes: helixPasses,
      };
      const tp = await camwosaApi.opDrechseln(werkzeugId, parameter);
      setErzeugt(tp);
      operationHinzufuegen({
        id: `dreh_${Date.now()}`,
        name: `Drechseln (${strategie})`,
        typ: "drechseln",
        werkzeug_id: werkzeugId,
        geometrie_id: null,
        parameter: parameter as any,
        toolpath: tp,
        aktiviert: true,
      });
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Fehler");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-xl font-bold">Drehen (Rotary)</h1>
        <p className="text-sm text-camwosa-muted">
          Fraeser haengt vertikal von oben, Werkstueck dreht sich langsam
          darunter — Rotary-Carving. (Nicht klassisches Drechseln mit
          Drehmeissel auf Drehbank.) Profil zeichnen, Parameter setzen, G-Code
          erzeugen.
        </p>
      </header>

      {/* Profil-Editor */}
      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">
          Profil (Halbschnitt)
          <span className="ml-2 text-xs font-normal text-camwosa-muted">
            X = Laengsachse, Radius = Abstand von der Drehachse
          </span>
        </h2>
        <DrechselProfilEditor
          profil={profil}
          onChange={setProfil}
          rohmaterial_radius_mm={rohRadius}
        />
        <div className="mt-2 flex gap-2 text-xs">
          <button
            className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
            onClick={() => setProfil(VASE_DEFAULT)}
          >
            Vase-Vorlage
          </button>
          <button
            className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
            onClick={() => setProfil([[0, 18], [100, 18]])}
          >
            Zylinder (Ø36×100)
          </button>
          <button
            className="rounded border border-camwosa-default px-2 py-1 hover:bg-camwosa-overlay"
            onClick={() => setProfil([[0, 25], [100, 15]])}
          >
            Kegel
          </button>
          <button
            className="rounded border border-red-700 px-2 py-1 hover:bg-red-900/40"
            onClick={() => setProfil([])}
          >
            Profil leeren
          </button>
        </div>
      </section>

      {/* Maschinen-/Strategie-Setup */}
      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Strategie + Maschinen-Setup</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Feld label="Werkzeug">
            <select
              value={werkzeugId}
              onChange={(e) => setWerkzeugId(e.target.value)}
              className="w-full rounded bg-camwosa-bg px-2 py-1"
            >
              <option value="">— waehlen —</option>
              {werkzeuge.map((w) => (
                <option key={w.id} value={w.id}>{w.name} ({w.durchmesser}mm)</option>
              ))}
            </select>
          </Feld>
          <Feld label="Strategie">
            <select
              value={strategie}
              onChange={(e) => setStrategie(e.target.value as DrechselStrategie)}
              className="w-full rounded bg-camwosa-bg px-2 py-1"
            >
              {(Object.entries(STRATEGIE_LABEL) as Array<[DrechselStrategie, string]>).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </Feld>
          <NumFeld label="Rohmaterial Ø/2 (mm)" v={rohRadius} on={setRohRadius} step={0.5} />
          <NumFeld label="Spindel RPM" v={spindelRpm} on={setSpindelRpm} step={500} />
          <NumFeld label="Werkstueck-Drehzahl (U/min)" v={drehzahl} on={setDrehzahl} step={10} />
          <NumFeld label="Vorschub (mm/min)" v={vorschub} on={setVorschub} step={50} />
          <NumFeld label="Eintauch-Vorschub (mm/min)" v={eintauchVorschub} on={setEintauchVorschub} step={50} />
          <NumFeld label="Stepdown Schruppen (mm)" v={stepdown} on={setStepdown} step={0.1} />
          <NumFeld label="Aufmass Schlichten (mm)" v={aufmass} on={setAufmass} step={0.1} />
          <NumFeld label="Schlicht-Zustellung (mm)" v={schlichtZustellung} on={setSchlichtZustellung} step={0.1} />
        </div>

        {istHelix && (
          <div className="mt-3 rounded border border-camwosa-info/40 bg-info-soft p-3">
            <h3 className="mb-2 flex items-center text-xs font-semibold text-camwosa-info">
              Helix-Parameter
              <FachTooltip {...FACHBEGRIFFE.drechseln_drehzahl} />
            </h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <NumFeld label="Steigung (mm/Umdrehung)" v={helixSteigung} on={setHelixSteigung} step={0.1} />
              <NumFeld label="Helix-Tiefe (mm)" v={helixTiefe} on={setHelixTiefe} step={0.1} />
              <NumFeld label="Anzahl Passes" v={helixPasses} on={(v) => setHelixPasses(Math.max(1, Math.round(v)))} step={1} />
            </div>
            {helixSyncFeed != null && (
              <p className="mt-2 text-xs text-camwosa-text">
                Synchronisierter X-Vorschub:{" "}
                <span className="font-mono">{helixSyncFeed.toFixed(0)} mm/min</span>{" "}
                <span className="text-camwosa-muted">(= {helixSteigung} mm/U × {drehzahl} U/min)</span>
              </p>
            )}
          </div>
        )}
      </section>

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
          {fehler}
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          className="rounded bg-camwosa-accent px-4 py-2 font-medium text-camwosa-bg hover:opacity-90 disabled:opacity-50"
          onClick={() => void erzeugen()}
          disabled={busy}
        >
          {busy ? "..." : "→ Toolpath erzeugen"}
        </button>
        {erzeugt && (
          <span className="text-xs text-camwosa-ok">
            ✓ {erzeugt.bewegungen.length} Bewegungen erzeugt — landet im Tab „Operationen"
          </span>
        )}
      </div>
    </div>
  );
}

function Feld({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-xs">
      <span className="mb-0.5 block text-camwosa-muted">{label}</span>
      {children}
    </label>
  );
}

function NumFeld({
  label, v, on, step,
}: { label: string; v: number; on: (v: number) => void; step: number }) {
  return (
    <Feld label={label}>
      <input
        type="number"
        step={step}
        value={v}
        onChange={(e) => on(Number(e.target.value))}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
    </Feld>
  );
}
