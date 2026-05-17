import { useState } from "react";
import type { Werkzeug } from "../api/types";

// Lokale Typen — spiegelt das Backend (Discriminated Union)
type Strategie = "separate_datei" | "inline_m6" | "inline_makro";

interface OperationSchritt {
  typ: "operation"; id: string; titel?: string; aktiviert?: boolean;
  operation_id: string;
}
interface WerkzeugWechselSchritt {
  typ: "werkzeugwechsel"; id: string; titel?: string; aktiviert?: boolean;
  werkzeug_neu_id: string;
  werkzeug_alt_id?: string | null;
  mensch_pause?: boolean;
  anweisung?: string;
  strategie?: Strategie;
  makro_name?: string | null;
  z_probe_nach_wechsel?: boolean;
}
interface ManualNCSchritt {
  typ: "manual_nc"; id: string; titel?: string; aktiviert?: boolean;
  gcode_zeilen: string[];
  sicher_anfahren?: boolean;
}
interface PauseSchritt {
  typ: "pause"; id: string; titel?: string; aktiviert?: boolean;
  anweisung: string;
}
interface UmspannSchritt {
  typ: "umspann"; id: string; titel?: string; aktiviert?: boolean;
  anweisung: string;
}

type Schritt =
  | OperationSchritt | WerkzeugWechselSchritt | ManualNCSchritt
  | PauseSchritt | UmspannSchritt;

interface Operation { id: string; name: string; typ: string }

interface Props {
  schritte: Schritt[];
  onChange: (s: Schritt[]) => void;
  operationen: Operation[];
  werkzeuge: Werkzeug[];
  /** Werkzeug das am Setup-Start montiert ist. */
  start_werkzeug_id?: string;
}

const ICON_PRO_TYP: Record<Schritt["typ"], string> = {
  operation: "⚙",
  werkzeugwechsel: "🔧",
  manual_nc: "{}",
  pause: "⏸",
  umspann: "⇄",
};

const LABEL_PRO_TYP: Record<Schritt["typ"], string> = {
  operation: "Operation",
  werkzeugwechsel: "Werkzeugwechsel",
  manual_nc: "Manual G-Code",
  pause: "Pause",
  umspann: "Umspannen",
};

const STRATEGIE_LABEL: Record<Strategie, string> = {
  separate_datei: "Separate G-Code-Datei (CNCjs laedt zwei Jobs)",
  inline_m6: "Inline M6 + M0 (Pause im G-Code, Resume nach Wechsel)",
  inline_makro: "Inline via CNCjs-Makro (z.B. mit Z-Probe)",
};

export default function SchrittListeEditor({
  schritte, onChange, operationen, werkzeuge, start_werkzeug_id,
}: Props) {
  const [offeneId, setOffeneId] = useState<string | null>(null);

  function update(idx: number, patch: Partial<Schritt>) {
    const neu = schritte.slice();
    neu[idx] = { ...neu[idx], ...patch } as Schritt;
    onChange(neu);
  }
  function loeschen(idx: number) {
    onChange(schritte.filter((_, i) => i !== idx));
  }
  function verschiebe(idx: number, richtung: -1 | 1) {
    const j = idx + richtung;
    if (j < 0 || j >= schritte.length) return;
    const neu = schritte.slice();
    [neu[idx], neu[j]] = [neu[j], neu[idx]];
    onChange(neu);
  }
  function neuerSchritt(typ: Schritt["typ"]) {
    const id = `s_${Date.now().toString(36)}`;
    let neu: Schritt;
    switch (typ) {
      case "operation":
        neu = { typ, id, operation_id: operationen[0]?.id ?? "" };
        break;
      case "werkzeugwechsel":
        neu = {
          typ, id,
          werkzeug_neu_id: werkzeuge[0]?.id ?? "",
          strategie: "separate_datei",
          mensch_pause: true,
          anweisung: "Werkzeug einsetzen, weiter mit Resume",
        };
        break;
      case "manual_nc":
        neu = { typ, id, gcode_zeilen: ["; eigene G-Code-Zeile"] };
        break;
      case "pause":
        neu = { typ, id, anweisung: "Bitte pruefen, dann weiter." };
        break;
      case "umspann":
        neu = { typ, id, anweisung: "Werkstueck neu spannen." };
        break;
    }
    onChange([...schritte, neu]);
    setOffeneId(id);
  }

  // Sequenz-Hilfe: zeige bei jedem Schritt, welches Werkzeug aktiv ist
  let aktiv = start_werkzeug_id ?? "";
  const wzProSchritt = schritte.map((s) => {
    if (s.typ === "werkzeugwechsel") aktiv = s.werkzeug_neu_id;
    return aktiv;
  });

  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-camwosa-muted">Schritt hinzufuegen:</span>
        {(Object.keys(LABEL_PRO_TYP) as Schritt["typ"][]).map((t) => (
          <button
            key={t}
            className="rounded border border-gray-600 px-2 py-1 text-xs hover:bg-gray-700"
            onClick={() => neuerSchritt(t)}
            title={`+ ${LABEL_PRO_TYP[t]}`}
          >
            <span className="mr-1">{ICON_PRO_TYP[t]}</span>
            + {LABEL_PRO_TYP[t]}
          </button>
        ))}
      </div>

      <ul className="space-y-2">
        {schritte.length === 0 && (
          <li className="rounded border border-dashed border-gray-700 p-4 text-center text-xs text-camwosa-muted">
            Noch keine Schritte. Tipp: typischer Workflow ist „Schruppen — Werkzeugwechsel — Schlichten".
          </li>
        )}
        {schritte.map((s, idx) => (
          <li
            key={s.id}
            className={[
              "rounded border bg-camwosa-surface",
              s.aktiviert === false ? "border-gray-800 opacity-50" : "border-gray-700",
              offeneId === s.id ? "ring-1 ring-camwosa-accent" : "",
            ].join(" ")}
          >
            <div className="flex items-center gap-2 px-2 py-1.5">
              <span className="w-6 text-center text-lg">{ICON_PRO_TYP[s.typ]}</span>
              <div className="flex-1 cursor-pointer"
                onClick={() => setOffeneId(offeneId === s.id ? null : s.id)}
              >
                <div className="text-sm font-medium">
                  {idx + 1}. {LABEL_PRO_TYP[s.typ]}
                  {s.typ === "operation" && (
                    <span className="ml-2 text-xs text-camwosa-muted">
                      — {operationen.find((o) => o.id === (s as OperationSchritt).operation_id)?.name ?? "?"}
                    </span>
                  )}
                  {s.typ === "werkzeugwechsel" && (
                    <span className="ml-2 text-xs text-camwosa-muted">
                      → {werkzeuge.find((w) => w.id === (s as WerkzeugWechselSchritt).werkzeug_neu_id)?.name ?? "?"}
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-camwosa-muted">
                  Aktives Werkzeug danach: {werkzeuge.find((w) => w.id === wzProSchritt[idx])?.name ?? "?"}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  className="rounded px-1 text-xs text-camwosa-muted hover:bg-gray-700"
                  onClick={() => verschiebe(idx, -1)} title="Nach oben">▲</button>
                <button
                  className="rounded px-1 text-xs text-camwosa-muted hover:bg-gray-700"
                  onClick={() => verschiebe(idx, 1)} title="Nach unten">▼</button>
                <input
                  type="checkbox"
                  checked={s.aktiviert !== false}
                  onChange={(e) => update(idx, { aktiviert: e.target.checked })}
                  title="Aktiviert"
                />
                <button
                  className="rounded border border-red-700 px-2 py-0.5 text-xs hover:bg-red-900/40"
                  onClick={() => loeschen(idx)}
                  title="Loeschen"
                >
                  🗑
                </button>
              </div>
            </div>

            {offeneId === s.id && (
              <div className="border-t border-gray-700 px-3 py-2">
                <SchrittForm
                  s={s}
                  operationen={operationen}
                  werkzeuge={werkzeuge}
                  onPatch={(p) => update(idx, p)}
                />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SchrittForm({
  s, operationen, werkzeuge, onPatch,
}: {
  s: Schritt;
  operationen: Operation[];
  werkzeuge: Werkzeug[];
  onPatch: (p: Partial<Schritt>) => void;
}) {
  switch (s.typ) {
    case "operation":
      return (
        <label className="block text-xs">
          <span className="mb-0.5 block text-camwosa-muted">Operation</span>
          <select
            className="w-full rounded bg-camwosa-bg px-2 py-1"
            value={(s as OperationSchritt).operation_id}
            onChange={(e) => onPatch({ operation_id: e.target.value } as Partial<OperationSchritt>)}
          >
            {operationen.map((o) => (
              <option key={o.id} value={o.id}>{o.name} ({o.typ})</option>
            ))}
          </select>
        </label>
      );

    case "werkzeugwechsel": {
      const ww = s as WerkzeugWechselSchritt;
      return (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <label className="text-xs">
            <span className="mb-0.5 block text-camwosa-muted">Neues Werkzeug</span>
            <select
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={ww.werkzeug_neu_id}
              onChange={(e) => onPatch({ werkzeug_neu_id: e.target.value } as Partial<WerkzeugWechselSchritt>)}
            >
              {werkzeuge.map((w) => (
                <option key={w.id} value={w.id}>{w.name} ({w.durchmesser}mm)</option>
              ))}
            </select>
          </label>
          <label className="text-xs">
            <span className="mb-0.5 block text-camwosa-muted">G-Code-Strategie</span>
            <select
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              value={ww.strategie ?? "separate_datei"}
              onChange={(e) => onPatch({ strategie: e.target.value as Strategie } as Partial<WerkzeugWechselSchritt>)}
            >
              {(Object.entries(STRATEGIE_LABEL) as Array<[Strategie, string]>).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          {ww.strategie === "inline_makro" && (
            <label className="text-xs sm:col-span-2">
              <span className="mb-0.5 block text-camwosa-muted">Makro-Name</span>
              <input
                className="w-full rounded bg-camwosa-bg px-2 py-1"
                value={ww.makro_name ?? ""}
                onChange={(e) => onPatch({ makro_name: e.target.value } as Partial<WerkzeugWechselSchritt>)}
                placeholder="z.B. TOOLCHANGE_PROBE"
              />
            </label>
          )}
          <label className="text-xs sm:col-span-2">
            <span className="mb-0.5 block text-camwosa-muted">Anweisung an den User</span>
            <textarea
              className="w-full rounded bg-camwosa-bg px-2 py-1"
              rows={2}
              value={ww.anweisung ?? ""}
              onChange={(e) => onPatch({ anweisung: e.target.value } as Partial<WerkzeugWechselSchritt>)}
            />
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={ww.z_probe_nach_wechsel ?? false}
              onChange={(e) => onPatch({ z_probe_nach_wechsel: e.target.checked } as Partial<WerkzeugWechselSchritt>)}
            />
            <span>Z-Probe nach Wechsel</span>
          </label>
        </div>
      );
    }

    case "manual_nc": {
      const m = s as ManualNCSchritt;
      return (
        <div className="space-y-2">
          <label className="text-xs">
            <span className="mb-0.5 block text-camwosa-muted">G-Code-Zeilen (eine pro Zeile)</span>
            <textarea
              className="h-32 w-full rounded bg-camwosa-bg px-2 py-1 font-mono text-xs"
              value={m.gcode_zeilen.join("\n")}
              onChange={(e) => onPatch({
                gcode_zeilen: e.target.value.split("\n"),
              } as Partial<ManualNCSchritt>)}
            />
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={m.sicher_anfahren !== false}
              onChange={(e) => onPatch({ sicher_anfahren: e.target.checked } as Partial<ManualNCSchritt>)}
            />
            <span>Vor dem Block auf Sicherheitshoehe fahren</span>
          </label>
        </div>
      );
    }

    case "pause":
    case "umspann":
      return (
        <label className="text-xs">
          <span className="mb-0.5 block text-camwosa-muted">Anweisung</span>
          <textarea
            className="w-full rounded bg-camwosa-bg px-2 py-1"
            rows={3}
            value={s.anweisung}
            onChange={(e) => onPatch({ anweisung: e.target.value } as Partial<PauseSchritt | UmspannSchritt>)}
          />
        </label>
      );
  }
}
