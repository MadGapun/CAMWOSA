/**
 * First-Run-Wizard nach Design-Note 6 (Design Exploration):
 * „CAMWOSA fokussiert auf die 4 Dinge die du einmal machst:
 *  Maschine, Spindel, ein Werkzeug, Materialien."
 *
 * Erscheint EINMALIG beim ersten Start, wenn keine aktive Maschine im Store ist.
 * Stellt 4 Schritte; pro Schritt kann der User zwischen „Vorhandene waehlen"
 * und „Neu anlegen" wechseln (Issue #22 + #23).
 *
 * Schreibt fertige Stammdaten in den Store + LocalStorage, dann verschwindet.
 * User kann ihn ueber „Einstellungen → Onboarding nochmal zeigen" wieder oeffnen.
 */

import { useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import type {
  ControllerTyp,
  MaschinenProfil,
  Material,
  MaterialKategorie,
  Spindel,
  SpindelTyp,
  Werkzeug,
  WerkzeugTyp,
} from "../api/types";

const WIZARD_DONE_KEY = "camwosa.firstRunDone";

type Modus = "vorhanden" | "neu";

export default function FirstRunWizard({
  onClose,
}: { onClose: () => void }) {
  const maschinen = useAppStore((s) => s.maschinen);
  const spindeln = useAppStore((s) => s.spindeln);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const materialien = useAppStore((s) => s.materialien);
  const setMaschinen = useAppStore((s) => s.setMaschinen);
  const setSpindeln = useAppStore((s) => s.setSpindeln);
  const setWerkzeuge = useAppStore((s) => s.setWerkzeuge);
  const setMaterialien = useAppStore((s) => s.setMaterialien);
  const setAktiveMaschine = useAppStore((s) => s.setAktiveMaschine);
  const setAktiveSpindelId = useAppStore((s) => s.setAktiveSpindelId);
  const setAktivesMaterial = useAppStore((s) => s.setAktivesMaterial);

  const [schritt, setSchritt] = useState(0);
  const [maschineId, setMaschineId] = useState("");
  const [spindelId, setSpindelId] = useState("");
  const [werkzeugId, setWerkzeugId] = useState("");
  const [materialId, setMaterialId] = useState("");

  // Modus pro Schritt — Default: Vorhandene (wenn vorhanden), sonst Neu
  const [modusMaschine, setModusMaschine] = useState<Modus>(maschinen.length ? "vorhanden" : "neu");
  const [modusSpindel, setModusSpindel] = useState<Modus>(spindeln.length ? "vorhanden" : "neu");
  const [modusWerkzeug, setModusWerkzeug] = useState<Modus>(werkzeuge.length ? "vorhanden" : "neu");
  const [modusMaterial, setModusMaterial] = useState<Modus>(materialien.length ? "vorhanden" : "neu");

  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  // --- Neu-Anlegen-Formulardaten -------------------------------------------
  const [neueMaschine, setNeueMaschine] = useState<NeueMaschineDaten>(defaultMaschine());
  const [neueSpindel, setNeueSpindel] = useState<NeueSpindelDaten>(defaultSpindel());
  const [neuesWerkzeug, setNeuesWerkzeug] = useState<NeuesWerkzeugDaten>(defaultWerkzeug());
  const [neuesMaterial, setNeuesMaterial] = useState<NeuesMaterialDaten>(defaultMaterial());

  const verfuegbareSpindeln = maschineId
    ? spindeln.filter((sp) =>
        maschinen.find((m) => m.id === maschineId)?.spindel_ids?.includes(sp.id),
      )
    : spindeln;

  // --- Anlege-Aktionen pro Schritt -----------------------------------------

  async function maschineAnlegen(): Promise<string | null> {
    setFehler(null);
    try {
      const payload: MaschinenProfil = {
        id: machbareId(neueMaschine.name, "machine"),
        name: neueMaschine.name.trim(),
        hersteller: neueMaschine.hersteller.trim() || "Eigenbau",
        modell: neueMaschine.modell.trim() || "Custom",
        controller: neueMaschine.controller,
        arbeitsraum: { x: neueMaschine.x, y: neueMaschine.y, z: neueMaschine.z },
        max_vorschub: neueMaschine.max_vorschub,
        sicherer_vorschub: Math.round(neueMaschine.max_vorschub * 0.6),
        eilgang: Math.round(neueMaschine.max_vorschub * 1.2),
        spindel_ids: [],
        aktive_spindel_id: null,
        spindel_typ: "manuell",
        spindel_rpm_min: 10000,
        spindel_rpm_max: 30000,
        sicherheitshoehe: 5.0,
        werkzeugwechsel_position: null,
        postprozessor: "grbl_genmitsu_pvxl",
        modi: ["standard_xyz"],
        aktiver_modus: "standard_xyz",
      };
      const res = await camwosaApi.maschineAnlegen(payload);
      const liste = await camwosaApi.maschinen();
      setMaschinen(liste);
      return res.maschine.id;
    } catch (e) {
      setFehler(httpFehler(e));
      return null;
    }
  }

  async function spindelAnlegen(): Promise<string | null> {
    setFehler(null);
    try {
      const payload: Spindel = {
        id: machbareId(neueSpindel.name, "spindel"),
        name: neueSpindel.name.trim(),
        hersteller: neueSpindel.hersteller.trim() || "Unbekannt",
        modell: neueSpindel.modell.trim() || "—",
        typ: neueSpindel.typ,
        rpm_min: neueSpindel.rpm_min,
        rpm_max: neueSpindel.rpm_max,
        kuehlung: "luft",
        herkunft: "upgrade",
      };
      const res = await camwosaApi.spindelAnlegen(payload);
      const liste = await camwosaApi.spindeln();
      setSpindeln(liste);
      // Optional: an die aktuelle Maschine binden
      if (maschineId) {
        const m = maschinen.find((x) => x.id === maschineId);
        if (m) {
          const updated: MaschinenProfil = {
            ...m,
            spindel_ids: Array.from(new Set([...(m.spindel_ids ?? []), res.spindel.id])),
            aktive_spindel_id: res.spindel.id,
          };
          await camwosaApi.maschineUpdaten(m.id, updated);
          const ml = await camwosaApi.maschinen();
          setMaschinen(ml);
        }
      }
      return res.spindel.id;
    } catch (e) {
      setFehler(httpFehler(e));
      return null;
    }
  }

  async function werkzeugAnlegen(): Promise<string | null> {
    setFehler(null);
    try {
      const payload: Werkzeug = {
        id: machbareId(neuesWerkzeug.name, "werkzeug"),
        name: neuesWerkzeug.name.trim(),
        typ: neuesWerkzeug.typ,
        durchmesser: neuesWerkzeug.durchmesser,
        schaft_durchmesser: neuesWerkzeug.schaft || neuesWerkzeug.durchmesser,
        schneidlaenge: neuesWerkzeug.schneidlaenge,
        gesamtlaenge: Math.max(neuesWerkzeug.schneidlaenge * 2.5, 30),
        schneiden: neuesWerkzeug.schneiden,
      };
      const res = await camwosaApi.werkzeugAnlegen(payload);
      const liste = await camwosaApi.werkzeuge();
      setWerkzeuge(liste);
      return res.werkzeug.id;
    } catch (e) {
      setFehler(httpFehler(e));
      return null;
    }
  }

  async function materialAnlegen(): Promise<string | null> {
    setFehler(null);
    try {
      const payload: Material = {
        id: machbareId(neuesMaterial.name, "material"),
        name: neuesMaterial.name.trim(),
        kategorie: neuesMaterial.kategorie,
        unter_kategorie: neuesMaterial.unter_kategorie || undefined,
        presets: [],
      };
      const res = await camwosaApi.materialAnlegen(payload);
      const liste = await camwosaApi.materialien();
      setMaterialien(liste);
      return res.material.id;
    } catch (e) {
      setFehler(httpFehler(e));
      return null;
    }
  }

  // --- Weiter-Logik pro Schritt --------------------------------------------

  async function weiter() {
    setLaeuft(true);
    try {
      if (schritt === 0) {
        if (modusMaschine === "neu") {
          const id = await maschineAnlegen();
          if (!id) return;
          setMaschineId(id);
        }
        if (!maschineId && modusMaschine === "vorhanden") return;
      } else if (schritt === 1) {
        if (modusSpindel === "neu") {
          const id = await spindelAnlegen();
          if (!id) return;
          setSpindelId(id);
        }
        if (!spindelId && modusSpindel === "vorhanden") return;
      } else if (schritt === 2) {
        if (modusWerkzeug === "neu") {
          const id = await werkzeugAnlegen();
          if (!id) return;
          setWerkzeugId(id);
        }
        if (!werkzeugId && modusWerkzeug === "vorhanden") return;
      } else if (schritt === 3) {
        if (modusMaterial === "neu") {
          const id = await materialAnlegen();
          if (!id) return;
          setMaterialId(id);
        }
        if (!materialId && modusMaterial === "vorhanden") return;
      }
      if (schritt < 3) setSchritt(schritt + 1);
      else fertig();
    } finally {
      setLaeuft(false);
    }
  }

  function fertig() {
    setAktiveMaschine(maschineId || null);
    if (spindelId) setAktiveSpindelId(spindelId);
    if (materialId) setAktivesMaterial(materialId);
    window.localStorage.setItem(WIZARD_DONE_KEY, "true");
    onClose();
  }

  // --- Pro-Schritt-Render --------------------------------------------------

  const titel = ["1 · Maschine", "2 · Spindel", "3 · Erstes Werkzeug", "4 · Material"][schritt];
  const hinweise = [
    "Welche CNC nutzt du? Du kannst eine vorhandene waehlen oder eine neue anlegen.",
    "Welche Spindel ist montiert? OEM-Router, Makita-Upgrade, Laser, ... — auch hier wahlweise neu.",
    "Welches Werkzeug spannst du als erstes ein? Du kannst spaeter beliebig viele anlegen.",
    "Womit faengst du an? Bestimmt die Standard-Feeds & Speeds fuer dein erstes Projekt.",
  ];

  const modusToggle = (
    <ModusSchalter
      modus={[
        modusMaschine, modusSpindel, modusWerkzeug, modusMaterial,
      ][schritt]}
      onChange={(m) => {
        if (schritt === 0) setModusMaschine(m);
        else if (schritt === 1) setModusSpindel(m);
        else if (schritt === 2) setModusWerkzeug(m);
        else setModusMaterial(m);
      }}
      vorhandenAnzahl={[
        maschinen.length, verfuegbareSpindeln.length, werkzeuge.length, materialien.length,
      ][schritt]}
    />
  );

  const kannWeiter =
    schritt === 0
      ? (modusMaschine === "neu" ? neueMaschine.name.trim().length > 1 : !!maschineId)
      : schritt === 1
      ? (modusSpindel === "neu" ? neueSpindel.name.trim().length > 1 : !!spindelId)
      : schritt === 2
      ? (modusWerkzeug === "neu" ? neuesWerkzeug.name.trim().length > 1 : !!werkzeugId)
      : (modusMaterial === "neu" ? neuesMaterial.name.trim().length > 1 : !!materialId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg border border-camwosa-default bg-camwosa-elevated shadow-lg">
        <header className="border-b border-camwosa-default p-4">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-camwosa-accent">
            Erst-Setup
          </div>
          <h2 className="text-lg font-semibold">{titel}</h2>
          <p className="mt-1 text-xs text-camwosa-muted">{hinweise[schritt]}</p>
          <div className="mt-3">{modusToggle}</div>
        </header>

        <div className="flex-1 overflow-auto p-4">
          {schritt === 0 && modusMaschine === "vorhanden" && (
            <Liste
              eintraege={maschinen.map((m) => ({
                id: m.id, titel: m.name,
                details: `${m.hersteller} ${m.modell} · Arbeitsraum ${m.arbeitsraum.x}×${m.arbeitsraum.y}×${m.arbeitsraum.z} mm`,
              }))}
              aktiv={maschineId}
              onWaehlen={setMaschineId}
            />
          )}
          {schritt === 0 && modusMaschine === "neu" && (
            <MaschineForm daten={neueMaschine} onChange={setNeueMaschine} />
          )}

          {schritt === 1 && modusSpindel === "vorhanden" && (
            <Liste
              eintraege={verfuegbareSpindeln.map((sp) => ({
                id: sp.id, titel: sp.name,
                details: `${sp.hersteller} ${sp.modell} · ${sp.rpm_min}-${sp.rpm_max} RPM · Typ: ${sp.typ}`,
              }))}
              aktiv={spindelId}
              onWaehlen={setSpindelId}
            />
          )}
          {schritt === 1 && modusSpindel === "neu" && (
            <SpindelForm daten={neueSpindel} onChange={setNeueSpindel} />
          )}

          {schritt === 2 && modusWerkzeug === "vorhanden" && (
            <Liste
              eintraege={werkzeuge.map((w) => ({
                id: w.id, titel: w.name,
                details: `${w.typ} · Ø ${w.durchmesser} mm · ${w.schneiden} Schneiden`,
              }))}
              aktiv={werkzeugId}
              onWaehlen={setWerkzeugId}
            />
          )}
          {schritt === 2 && modusWerkzeug === "neu" && (
            <WerkzeugForm daten={neuesWerkzeug} onChange={setNeuesWerkzeug} />
          )}

          {schritt === 3 && modusMaterial === "vorhanden" && (
            <Liste
              eintraege={materialien.map((m) => ({
                id: m.id, titel: m.name,
                details: `${m.kategorie}${m.unter_kategorie ? " · " + m.unter_kategorie : ""}`,
              }))}
              aktiv={materialId}
              onWaehlen={setMaterialId}
            />
          )}
          {schritt === 3 && modusMaterial === "neu" && (
            <MaterialForm daten={neuesMaterial} onChange={setNeuesMaterial} />
          )}

          {fehler && (
            <div className="mt-3 rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
              {fehler}
            </div>
          )}
        </div>

        <footer className="flex items-center justify-between gap-2 border-t border-camwosa-default p-3">
          <div className="flex gap-1">
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className={`h-1.5 w-8 rounded ${
                  i < schritt ? "bg-camwosa-accent"
                  : i === schritt ? "bg-camwosa-accent/60"
                  : "bg-camwosa-default"
                }`}
              />
            ))}
          </div>
          <div className="flex gap-2">
            <button
              className="rounded border border-camwosa-default px-3 py-1 text-xs hover:bg-camwosa-overlay"
              onClick={onClose}
              disabled={laeuft}
            >
              Spaeter
            </button>
            {schritt > 0 && (
              <button
                className="rounded border border-camwosa-default px-3 py-1 text-xs hover:bg-camwosa-overlay"
                onClick={() => setSchritt(schritt - 1)}
                disabled={laeuft}
              >
                ← Zurueck
              </button>
            )}
            <button
              className="rounded bg-camwosa-accent px-4 py-1 text-xs font-medium text-camwosa-bg disabled:opacity-50"
              onClick={() => void weiter()}
              disabled={!kannWeiter || laeuft}
            >
              {laeuft ? "..." : schritt < 3 ? "Weiter →" : "✓ Fertig"}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

// =============================================================================
// Formular-Komponenten — minimal, nur die Pflichtfelder. Voll-Editor spaeter.
// =============================================================================

interface NeueMaschineDaten {
  name: string; hersteller: string; modell: string;
  controller: ControllerTyp;
  x: number; y: number; z: number;
  max_vorschub: number;
}
function defaultMaschine(): NeueMaschineDaten {
  return {
    name: "", hersteller: "", modell: "",
    controller: "GRBL", x: 400, y: 400, z: 110,
    max_vorschub: 3000,
  };
}
function MaschineForm({
  daten, onChange,
}: { daten: NeueMaschineDaten; onChange: (d: NeueMaschineDaten) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 text-xs">
      <Feld label="Name *" tipp="z.B. 'ProVerXL 4030 V2 - meine'">
        <input type="text" className={cls} autoFocus
          value={daten.name} onChange={(e) => onChange({ ...daten, name: e.target.value })} />
      </Feld>
      <Feld label="Controller">
        <select className={cls} value={daten.controller}
          onChange={(e) => onChange({ ...daten, controller: e.target.value as ControllerTyp })}>
          {["GRBL", "Marlin", "LinuxCNC", "Mach3", "Duet", "Sonstige"].map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </Feld>
      <Feld label="Hersteller"><input type="text" className={cls}
        value={daten.hersteller} onChange={(e) => onChange({ ...daten, hersteller: e.target.value })} /></Feld>
      <Feld label="Modell"><input type="text" className={cls}
        value={daten.modell} onChange={(e) => onChange({ ...daten, modell: e.target.value })} /></Feld>
      <Feld label="Arbeitsraum X (mm)"><Nr v={daten.x} onChange={(v) => onChange({ ...daten, x: v })} min={50} /></Feld>
      <Feld label="Arbeitsraum Y (mm)"><Nr v={daten.y} onChange={(v) => onChange({ ...daten, y: v })} min={50} /></Feld>
      <Feld label="Arbeitsraum Z (mm)"><Nr v={daten.z} onChange={(v) => onChange({ ...daten, z: v })} min={20} /></Feld>
      <Feld label="Max. Vorschub (mm/min)" tipp="ProVerXL: 3000">
        <Nr v={daten.max_vorschub} onChange={(v) => onChange({ ...daten, max_vorschub: v })} min={100} step={100} />
      </Feld>
    </div>
  );
}

interface NeueSpindelDaten {
  name: string; hersteller: string; modell: string;
  typ: SpindelTyp; rpm_min: number; rpm_max: number;
}
function defaultSpindel(): NeueSpindelDaten {
  return { name: "", hersteller: "", modell: "", typ: "manuell", rpm_min: 10000, rpm_max: 30000 };
}
function SpindelForm({
  daten, onChange,
}: { daten: NeueSpindelDaten; onChange: (d: NeueSpindelDaten) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 text-xs">
      <Feld label="Name *" tipp="z.B. 'Makita RT0700'">
        <input type="text" className={cls} autoFocus
          value={daten.name} onChange={(e) => onChange({ ...daten, name: e.target.value })} />
      </Feld>
      <Feld label="Typ" tipp="manuell = nur RPM-Vorgabe, PWM = ueber GRBL S-Wert">
        <select className={cls} value={daten.typ}
          onChange={(e) => onChange({ ...daten, typ: e.target.value as SpindelTyp })}>
          <option value="manuell">manuell</option>
          <option value="PWM">PWM</option>
          <option value="analog">analog</option>
        </select>
      </Feld>
      <Feld label="Hersteller"><input type="text" className={cls}
        value={daten.hersteller} onChange={(e) => onChange({ ...daten, hersteller: e.target.value })} /></Feld>
      <Feld label="Modell"><input type="text" className={cls}
        value={daten.modell} onChange={(e) => onChange({ ...daten, modell: e.target.value })} /></Feld>
      <Feld label="RPM min"><Nr v={daten.rpm_min} onChange={(v) => onChange({ ...daten, rpm_min: v })} min={0} step={500} /></Feld>
      <Feld label="RPM max"><Nr v={daten.rpm_max} onChange={(v) => onChange({ ...daten, rpm_max: v })} min={100} step={500} /></Feld>
    </div>
  );
}

interface NeuesWerkzeugDaten {
  name: string; typ: WerkzeugTyp;
  durchmesser: number; schaft: number;
  schneidlaenge: number; schneiden: number;
}
function defaultWerkzeug(): NeuesWerkzeugDaten {
  return { name: "", typ: "schaftfraeser", durchmesser: 3, schaft: 0, schneidlaenge: 12, schneiden: 2 };
}
function WerkzeugForm({
  daten, onChange,
}: { daten: NeuesWerkzeugDaten; onChange: (d: NeuesWerkzeugDaten) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 text-xs">
      <Feld label="Name *" tipp="z.B. 'Schaftfraeser Ø3 HSS'">
        <input type="text" className={cls} autoFocus
          value={daten.name} onChange={(e) => onChange({ ...daten, name: e.target.value })} />
      </Feld>
      <Feld label="Typ">
        <select className={cls} value={daten.typ}
          onChange={(e) => onChange({ ...daten, typ: e.target.value as WerkzeugTyp })}>
          {[
            ["schaftfraeser", "Schaftfraeser"],
            ["kugelfraeser", "Kugelfraeser"],
            ["torusfraeser", "Torusfraeser"],
            ["v_bit", "V-Bit"],
            ["gravierstichel", "Gravierstichel"],
            ["bohrer", "Bohrer"],
            ["einschneider", "Einschneider"],
            ["fischschwanz", "Fischschwanz"],
            ["schruppfraeser", "Schruppfraeser"],
            ["diamantgravierer", "Diamantgravierer"],
          ].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </Feld>
      <Feld label="Durchmesser (mm)"><Nr v={daten.durchmesser} onChange={(v) => onChange({ ...daten, durchmesser: v })} min={0.1} step={0.1} /></Feld>
      <Feld label="Schaft-Ø (mm)" tipp="0 = nutzt Werkzeug-Ø">
        <Nr v={daten.schaft} onChange={(v) => onChange({ ...daten, schaft: v })} min={0} step={0.1} />
      </Feld>
      <Feld label="Schneidlaenge (mm)"><Nr v={daten.schneidlaenge} onChange={(v) => onChange({ ...daten, schneidlaenge: v })} min={0.5} step={0.5} /></Feld>
      <Feld label="Schneiden"><Nr v={daten.schneiden} onChange={(v) => onChange({ ...daten, schneiden: v })} min={1} max={8} step={1} /></Feld>
    </div>
  );
}

interface NeuesMaterialDaten {
  name: string; kategorie: MaterialKategorie; unter_kategorie: string;
}
function defaultMaterial(): NeuesMaterialDaten {
  return { name: "", kategorie: "holz", unter_kategorie: "" };
}
function MaterialForm({
  daten, onChange,
}: { daten: NeuesMaterialDaten; onChange: (d: NeuesMaterialDaten) => void }) {
  return (
    <div className="grid grid-cols-2 gap-3 text-xs">
      <Feld label="Name *" tipp="z.B. 'Buche massiv'">
        <input type="text" className={cls} autoFocus
          value={daten.name} onChange={(e) => onChange({ ...daten, name: e.target.value })} />
      </Feld>
      <Feld label="Kategorie">
        <select className={cls} value={daten.kategorie}
          onChange={(e) => onChange({ ...daten, kategorie: e.target.value as MaterialKategorie })}>
          {[
            ["holz", "Holz (Massiv)"],
            ["holzwerkstoff", "Holzwerkstoff (MDF/Sperr.)"],
            ["kunststoff", "Kunststoff"],
            ["ne_metall", "NE-Metall (Alu/Messing)"],
            ["metall", "Metall (Stahl)"],
            ["sonstiges", "Sonstiges"],
          ].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </Feld>
      <Feld label="Unter-Kategorie (optional)">
        <input type="text" className={cls}
          value={daten.unter_kategorie}
          onChange={(e) => onChange({ ...daten, unter_kategorie: e.target.value })} />
      </Feld>
      <div className="col-span-2 mt-1 text-[11px] text-camwosa-muted">
        Hinweis: Feeds &amp; Speeds-Presets kannst du spaeter im Material-Editor
        hinzufuegen — fuer den Erststart reicht der Name.
      </div>
    </div>
  );
}

// =============================================================================
// Helfer
// =============================================================================

const cls = "w-full rounded border border-camwosa-default bg-camwosa-bg px-2 py-1 text-xs";

function ModusSchalter({
  modus, onChange, vorhandenAnzahl,
}: { modus: Modus; onChange: (m: Modus) => void; vorhandenAnzahl: number }) {
  return (
    <div className="flex w-fit overflow-hidden rounded border border-camwosa-default text-xs">
      <button
        type="button"
        className={`px-3 py-1 ${modus === "vorhanden" ? "bg-camwosa-accent text-camwosa-bg" : "text-camwosa-muted hover:bg-camwosa-overlay"}`}
        onClick={() => onChange("vorhanden")}
        disabled={vorhandenAnzahl === 0}
        title={vorhandenAnzahl === 0 ? "Keine vorhanden — bitte neu anlegen" : ""}
      >
        Vorhandene waehlen ({vorhandenAnzahl})
      </button>
      <button
        type="button"
        className={`px-3 py-1 ${modus === "neu" ? "bg-camwosa-accent text-camwosa-bg" : "text-camwosa-muted hover:bg-camwosa-overlay"}`}
        onClick={() => onChange("neu")}
      >
        + Neu anlegen
      </button>
    </div>
  );
}

function Feld({
  label, tipp, children,
}: { label: string; tipp?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-0.5 block text-camwosa-muted" title={tipp}>{label}</span>
      {children}
    </label>
  );
}

function Nr({
  v, onChange, min, max, step = 1,
}: { v: number; onChange: (v: number) => void; min?: number; max?: number; step?: number }) {
  return (
    <input
      type="number" className={cls}
      value={v}
      min={min} max={max} step={step}
      onChange={(e) => {
        const n = parseFloat(e.target.value);
        if (!Number.isNaN(n)) onChange(n);
      }}
    />
  );
}

function Liste({
  eintraege, aktiv, onWaehlen,
}: {
  eintraege: Array<{ id: string; titel: string; details: string }>;
  aktiv: string;
  onWaehlen: (id: string) => void;
}) {
  if (!eintraege.length) {
    return (
      <p className="text-xs text-camwosa-muted">
        Keine vorhandenen Eintraege — wechsle oben auf „Neu anlegen".
      </p>
    );
  }
  return (
    <ul className="space-y-1.5">
      {eintraege.map((e) => (
        <li key={e.id}>
          <button
            onClick={() => onWaehlen(e.id)}
            className={`w-full rounded border p-3 text-left text-sm transition ${
              aktiv === e.id
                ? "border-camwosa-accent bg-camwosa-accent-soft"
                : "border-camwosa-default bg-camwosa-surface hover:border-camwosa-accent/60"
            }`}
          >
            <div className="font-medium">{e.titel}</div>
            <div className="text-xs text-camwosa-muted">{e.details}</div>
          </button>
        </li>
      ))}
    </ul>
  );
}

function machbareId(name: string, prefix: string): string {
  const slug = name.toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 40) || "neu";
  const suffix = Date.now().toString(36).slice(-4);
  return `user_${prefix}_${slug}_${suffix}`;
}

function httpFehler(e: unknown): string {
  if (e && typeof e === "object" && "response" in e) {
    const r = (e as { response?: { data?: { fehler?: string } } }).response;
    if (r?.data?.fehler) return r.data.fehler;
  }
  return e instanceof Error ? e.message : String(e);
}

/** Hilfsfunktion: hat der User den Wizard schon einmal abgeschlossen? */
export function firstRunErledigt(): boolean {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(WIZARD_DONE_KEY) === "true";
}

/** Wizard erneut zeigen lassen (vom Einstellungen-View). */
export function firstRunZuruecksetzen() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(WIZARD_DONE_KEY);
  }
}
