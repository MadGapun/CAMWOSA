import { useRef, useState } from "react";
import Editor, { type BeforeMount, type OnMount } from "@monaco-editor/react";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import { camwosaApi } from "../api/client";
import { useAktiveMaschine, useAktiveSpindel, useAppStore } from "../state/store";
import { useWorkflowStore, type WerkstueckTransformation } from "../state/workflowStore";
import { BEFEHLE, findeBefehl, type GCodeBefehl } from "../components/GCodeBibliothek";
import {
  registriereGcodeHighlighting,
  SPRACHE_ID as GCODE_SPRACHE,
  THEME_ID as GCODE_THEME,
} from "../components/gcodeHighlighter";

const KAT_LABEL: Record<GCodeBefehl["kategorie"], string> = {
  bewegung: "Bewegung",
  spindel: "Spindel",
  werkzeug: "Werkzeug / Pause",
  koord: "Koordinaten",
  einheit: "Einheiten",
  ende: "Programm-Ende",
};

/** A49: Hat die Transformation überhaupt eine Wirkung (≠ Identität)? */
function istAktiveTransformation(tf?: WerkstueckTransformation | null): boolean {
  if (!tf) return false;
  return (
    (!!tf.spiegeln && tf.spiegeln !== "keine") ||
    !!tf.drehung_grad ||
    !!tf.invertiere_z ||
    !!(tf.offset && tf.offset.some((v) => v !== 0))
  );
}

/** A49: Kurzbeschreibung einer Umspann-Lage für die Auswahl. */
function beschreibeTransformation(tf?: WerkstueckTransformation | null): string {
  if (!tf) return "keine";
  const teile: string[] = [];
  if (tf.spiegeln === "x") teile.push("an X gespiegelt");
  else if (tf.spiegeln === "y") teile.push("an Y gespiegelt");
  if (tf.drehung_grad) teile.push(`${tf.drehung_grad}° gedreht`);
  if (tf.invertiere_z) teile.push("gewendet (Z)");
  return teile.join(", ") || "keine";
}

const BEISPIEL = `; CAMWOSA G-Code (Beispiel)
G21
G90
G17
G94
M3 S18000
G0 X0 Y0 Z5
G1 Z-2 F400
G1 X100 Y0 F2000
G1 X100 Y50
G1 X0 Y50
G1 X0 Y0
G0 Z5
M5
M30
`;

export default function GCodeEditorView() {
  const { t } = useTranslation();
  const maschine = useAktiveMaschine();
  const aktiveSpindel = useAktiveSpindel();
  const operationen = useAppStore((s) => s.operationen);
  const aktiveOps = operationen.filter((o) => o.aktiviert && o.toolpath);
  // A49: Setups mit echter Umspann-Lage → Werkstück-Lage beim Export wählbar.
  const setups = useWorkflowStore((s) => s.setups);
  const umspannSetups = setups.filter((s) => istAktiveTransformation(s.transformation));
  const [umspannSetupId, setUmspannSetupId] = useState<string | null>(null);
  const aktiveTransformation =
    umspannSetups.find((s) => s.id === umspannSetupId)?.transformation ?? null;
  // Footgun-Warnung: Spiegeln ohne Werkstückmaß spiegelt um 0 → negative Koordinaten.
  const spiegelOhneMass =
    !!aktiveTransformation &&
    aktiveTransformation.spiegeln !== "keine" &&
    !aktiveTransformation.werkstueck_breite_mm &&
    !aktiveTransformation.werkstueck_tiefe_mm;

  const [value, setValue] = useState<string>(BEISPIEL);
  const [aktiverBefehl, setAktiverBefehl] = useState<GCodeBefehl | null>(null);
  const [filter, setFilter] = useState("");
  const [generieren, setGenerieren] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  // J9/J10: intelligente Fahrwege beim Export (einstellbar)
  const [fahrwegOpt, setFahrwegOpt] = useState(true);
  const [freifahrtAktiv, setFreifahrtAktiv] = useState(false);
  const [freifahrt, setFreifahrt] = useState(1);
  // Cluster P: Output-Härtung
  const [modal, setModal] = useState(true);
  const [rapidSafety, setRapidSafety] = useState(true);
  // J5: Rampen-Eintauchen + Q2: Rampen-Feed-Faktor (variable Eintauchgeschwindigkeit)
  const [rampe, setRampe] = useState(false);
  const [rampenWinkel, setRampenWinkel] = useState(5);
  const [rampenFaktor, setRampenFaktor] = useState(1);
  // Warmlauf am Programmstart (optional, VFD/Lager schonen). Defaults aus Spindel.
  const [warmlauf, setWarmlauf] = useState(false);
  const [warmlaufS, setWarmlaufS] = useState(aktiveSpindel?.warmlauf_zeit_s ?? 10);
  const [warmlaufRpm, setWarmlaufRpm] = useState(aktiveSpindel?.warmlauf_rpm ?? 8000);
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  const beforeMount: BeforeMount = (m) => {
    registriereGcodeHighlighting(m);
  };

  function onMount(editor: Parameters<OnMount>[0]) {
    editorRef.current = editor;
    editor.onDidChangeCursorPosition(() => {
      const pos = editor.getPosition();
      const model = editor.getModel();
      if (!pos || !model) return;
      const zeile = model.getLineContent(pos.lineNumber);
      setAktiverBefehl(findeBefehl(zeile));
    });
  }

  async function generierenAusOperationen() {
    if (!maschine) {
      setFehler("Bitte zuerst eine Maschine im Projekt waehlen.");
      return;
    }
    if (aktiveOps.length === 0) {
      setFehler("Keine berechneten Toolpaths vorhanden.");
      return;
    }
    setGenerieren(true);
    setFehler(null);
    try {
      const werkzeug_id = aktiveOps[0].werkzeug_id;
      const result = await camwosaApi.postprocess(
        maschine.id,
        werkzeug_id,
        aktiveOps.map((o) => o.toolpath!),
        undefined,
        {
          fahrweg_optimierung: fahrwegOpt,
          freifahrt_hoehe: freifahrtAktiv ? freifahrt : null,
          modal,
          rapid_safety: rapidSafety,
          rampe_eintauchen: rampe,
          rampen_winkel_grad: rampenWinkel,
          rampen_vorschub_faktor: rampenFaktor,
          // P1: Hochlauf-Dwell folgt der im UI gewählten (aktiven) Spindel
          spindel_hochlauf_s: aktiveSpindel?.rampen_zeit_s ?? null,
          // A49: Werkstück-Lage (Umspannung) — gewählte Transformation anwenden
          transformation: aktiveTransformation,
          // Warmlauf am Programmstart — nur wenn aktiviert
          warmlauf,
          warmlauf_s: warmlauf ? warmlaufS : null,
          warmlauf_rpm: warmlauf ? warmlaufRpm : null,
        },
      );
      setValue(result.gcode);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setFehler(msg);
    } finally {
      setGenerieren(false);
    }
  }

  function exportieren() {
    const blob = new Blob([value], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "camwosa.nc";
    a.click();
    URL.revokeObjectURL(url);
  }

  const gefiltert = BEFEHLE.filter((b) => {
    if (!filter) return true;
    const f = filter.toLowerCase();
    return (
      b.code.toLowerCase().includes(f) ||
      b.titel.toLowerCase().includes(f) ||
      b.beschreibung.toLowerCase().includes(f)
    );
  });

  const grouped = gefiltert.reduce<Record<string, GCodeBefehl[]>>((acc, b) => {
    (acc[b.kategorie] ??= []).push(b);
    return acc;
  }, {});

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("navigation.editor")}</h1>
        <div className="flex gap-2">
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
            onClick={() => void generierenAusOperationen()}
            disabled={generieren || aktiveOps.length === 0}
          >
            {generieren ? "Generiere..." : "Aus Operationen generieren"}
          </button>
          <button
            className="rounded border border-gray-600 px-3 py-1 text-xs"
            onClick={exportieren}
          >
            Exportieren (.nc)
          </button>
        </div>
      </div>

      {/* J9/J10: intelligente Fahrwege — einstellbar vor dem Generieren */}
      <div className="flex flex-wrap items-center gap-4 rounded border border-gray-700 bg-camwosa-surface px-3 py-1.5 text-xs">
        <span className="font-semibold text-camwosa-muted">Fahrwege:</span>
        <label className="flex items-center gap-1.5" title="Reihenfolge der Schnitte per Nearest-Neighbor optimieren → kürzere Eilgang-Wege, kürzere Zeit.">
          <input type="checkbox" checked={fahrwegOpt} onChange={(e) => setFahrwegOpt(e.target.checked)} />
          Kurze Wege (Reihenfolge optimieren)
        </label>
        <label className="flex items-center gap-1.5" title="Zwischen-Freifahrten knapp über die Geometrie senken statt auf voller Sicherheitshöhe. Erste Anfahrt + letzter Rückzug bleiben sicher.">
          <input type="checkbox" checked={freifahrtAktiv} onChange={(e) => setFreifahrtAktiv(e.target.checked)} />
          Knappe Freifahrt-Höhe
        </label>
        <span className={freifahrtAktiv ? "flex items-center gap-1" : "flex items-center gap-1 opacity-40"}>
          <input
            type="number" step={0.5} min={0} value={freifahrt}
            disabled={!freifahrtAktiv}
            onChange={(e) => setFreifahrt(Number(e.target.value))}
            className="w-16 rounded bg-camwosa-bg px-2 py-0.5"
          />
          mm über Geometrie
        </span>
        <span className="mx-1 text-camwosa-muted">·</span>
        <span className="font-semibold text-camwosa-muted">Output:</span>
        <label className="flex items-center gap-1.5" title="Redundante Achsworte/Vorschub entfernen → kleinere, sauberere Datei (bahn-identisch).">
          <input type="checkbox" checked={modal} onChange={(e) => setModal(e.target.checked)} />
          Modal (kompakt)
        </label>
        <label className="flex items-center gap-1.5" title="Diagonale Eilgänge in sichere Reihenfolge splitten (Z-hoch zuerst beim Rückzug).">
          <input type="checkbox" checked={rapidSafety} onChange={(e) => setRapidSafety(e.target.checked)} />
          Sichere Eilgänge
        </label>
        <span className="mx-1 text-camwosa-muted">·</span>
        <label className="flex items-center gap-1.5" title="Senkrechtes Eintauchen durch schräge Rampen ersetzen (schont den Fräser). Bahn bleibt identisch.">
          <input type="checkbox" checked={rampe} onChange={(e) => setRampe(e.target.checked)} />
          Rampen-Eintauchen
        </label>
        <span className={rampe ? "flex items-center gap-1" : "flex items-center gap-1 opacity-40"}>
          <input
            type="number" step={1} min={1} max={45} value={rampenWinkel}
            disabled={!rampe}
            onChange={(e) => setRampenWinkel(Number(e.target.value))}
            className="w-14 rounded bg-camwosa-bg px-2 py-0.5"
          />
          ° Winkel ·
          <input
            type="number" step={0.5} min={1} max={5} value={rampenFaktor}
            disabled={!rampe}
            onChange={(e) => setRampenFaktor(Number(e.target.value))}
            className="w-14 rounded bg-camwosa-bg px-2 py-0.5"
            title="Rampe darf schneller eintauchen als senkrecht (× Eintauch-Vorschub)"
          />
          × Feed
        </span>
        <span className="mx-1 text-camwosa-muted">·</span>
        <label
          className="flex items-center gap-1.5"
          title="Spindel am Programmstart kurz warmlaufen lassen (schont VFD/Lager). Sie dreht bei moderater Drehzahl, danach startet der Job."
        >
          <input type="checkbox" checked={warmlauf} onChange={(e) => setWarmlauf(e.target.checked)} />
          Warmlauf
        </label>
        <span className={warmlauf ? "flex items-center gap-1" : "flex items-center gap-1 opacity-40"}>
          <input
            type="number" step={1} min={1} max={120} value={warmlaufS}
            disabled={!warmlauf}
            onChange={(e) => setWarmlaufS(Number(e.target.value))}
            className="w-14 rounded bg-camwosa-bg px-2 py-0.5"
          />
          s @
          <input
            type="number" step={500} min={1} value={warmlaufRpm}
            disabled={!warmlauf}
            onChange={(e) => setWarmlaufRpm(Number(e.target.value))}
            className="w-20 rounded bg-camwosa-bg px-2 py-0.5"
          />
          U/min
        </span>
        {umspannSetups.length > 0 && (
          <>
            <span className="mx-1 text-camwosa-muted">·</span>
            <label
              className="flex items-center gap-1.5"
              title="A49: Werkstück-Lage beim Umspannen. Die gewählte Transformation (Spiegeln/Drehen/Wenden) wird vor dem Generieren auf ALLE Toolpaths angewendet — für 2-/N-seitige Bearbeitung. Bögen werden automatisch korrekt umgedreht."
            >
              <span className="font-semibold text-camwosa-muted">Werkstück-Lage:</span>
              <select
                className="rounded bg-camwosa-bg px-2 py-0.5"
                value={umspannSetupId ?? ""}
                onChange={(e) => setUmspannSetupId(e.target.value || null)}
              >
                <option value="">Original (keine Umspannung)</option>
                {umspannSetups.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} — {beschreibeTransformation(s.transformation)}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
      </div>

      {spiegelOhneMass && (
        <div className="rounded border border-camwosa-warn bg-amber-950/30 p-2 text-xs text-camwosa-warn">
          Achtung: Die gewählte Werkstück-Lage spiegelt, aber es ist kein
          Werkstückmaß (B×T) hinterlegt. Ohne Maß wird um die Null-Linie gespiegelt
          → negative Koordinaten. Trage die Werkstück-Breite/Tiefe im Setup
          (Workflow-Ansicht) nach.
        </div>
      )}

      {fehler && (
        <div className="rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
          {fehler}
        </div>
      )}

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-9 overflow-hidden rounded border border-gray-700">
          <Editor
            height="70vh"
            defaultLanguage={GCODE_SPRACHE}
            language={GCODE_SPRACHE}
            value={value}
            onChange={(v) => setValue(v ?? "")}
            beforeMount={beforeMount}
            onMount={onMount}
            theme={GCODE_THEME}
            options={{
              minimap: { enabled: true },
              fontSize: 13,
              wordWrap: "off",
              lineNumbers: "on",
              fontFamily: "'JetBrains Mono', ui-monospace, Menlo, monospace",
              renderWhitespace: "selection",
            }}
          />
        </div>

        <aside className="col-span-3 space-y-3">
          {aktiverBefehl ? (
            <section className="rounded border border-camwosa-accent bg-camwosa-surface p-3">
              <h3 className="text-sm font-semibold text-camwosa-accent">
                {aktiverBefehl.code} — {aktiverBefehl.titel}
              </h3>
              <p className="mt-2 text-xs">{aktiverBefehl.beschreibung}</p>
              {aktiverBefehl.beispiel && (
                <pre className="mt-2 rounded bg-camwosa-bg p-2 text-xs">
                  {aktiverBefehl.beispiel}
                </pre>
              )}
            </section>
          ) : (
            <section className="rounded border border-gray-700 bg-camwosa-surface p-3 text-xs text-camwosa-muted">
              Klick in eine Zeile mit G/M-Befehl fuer Erklaerung.
            </section>
          )}

          <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
            <h3 className="mb-2 text-sm font-semibold">Befehlsbibliothek</h3>
            <input
              type="text"
              className="mb-2 w-full rounded bg-camwosa-bg px-2 py-1 text-xs"
              placeholder="Suche..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <div className="max-h-[50vh] space-y-2 overflow-auto">
              {Object.entries(grouped).map(([kat, items]) => (
                <div key={kat}>
                  <h4 className="mb-1 text-xs font-semibold uppercase text-camwosa-muted">
                    {KAT_LABEL[kat as GCodeBefehl["kategorie"]]}
                  </h4>
                  <ul className="space-y-1">
                    {items.map((b) => (
                      <li
                        key={b.code}
                        className={clsx(
                          "cursor-pointer rounded px-2 py-1 text-xs hover:bg-gray-700",
                          aktiverBefehl?.code === b.code && "bg-camwosa-accent/30",
                        )}
                        onClick={() => setAktiverBefehl(b)}
                      >
                        <span className="font-mono text-camwosa-accent">{b.code}</span>{" "}
                        — {b.titel}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
