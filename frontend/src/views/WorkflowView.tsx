import { useState } from "react";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import { useAktiveMaschine, useAppStore } from "../state/store";
import {
  neueSetup,
  type Setup,
  type SetupPause,
  type SetupPauseTyp,
  useWorkflowStore,
} from "../state/workflowStore";
import { camwosaApi } from "../api/client";
import FotoSlot from "../components/FotoSlot";

const PAUSE_LABEL: Record<SetupPauseTyp, string> = {
  werkzeugwechsel: "Werkzeugwechsel",
  umspann: "Umspannen",
  werkstueck_verschieben: "Werkstueck verschieben",
  spindel_wechsel: "Spindel wechseln",
  optionaler_stop: "Optionaler Stop",
};

export default function WorkflowView() {
  const { t } = useTranslation();
  const maschine = useAktiveMaschine();
  const werkzeuge = useAppStore((s) => s.werkzeuge);

  const setups = useWorkflowStore((s) => s.setups);
  const hinzufuegen = useWorkflowStore((s) => s.hinzufuegen);
  const aktualisieren = useWorkflowStore((s) => s.aktualisieren);
  const loeschen = useWorkflowStore((s) => s.loeschen);
  const verschieben = useWorkflowStore((s) => s.verschieben);
  const pauseSetzen = useWorkflowStore((s) => s.pauseSetzen);
  const erledigt = useWorkflowStore((s) => s.erledigt);
  const toggleErledigt = useWorkflowStore((s) => s.toggleErledigt);
  const alleZuruecksetzen = useWorkflowStore((s) => s.alleZuruecksetzen);

  const [pruefBericht, setPruefBericht] = useState<{
    hat_blocker: boolean;
    probleme: Array<{ setup_id: string | null; stufe: string; text: string }>;
  } | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [projektName, setProjektName] = useState("Mein Projekt");

  function neuesSetupAnlegen() {
    if (werkzeuge.length === 0) return;
    hinzufuegen(neueSetup(`Setup ${setups.length + 1}`, werkzeuge[0].id));
  }

  function varianteFuerBackend() {
    return {
      id: "v1",
      name: "Default",
      rohmaterial: {
        form: "platte",
        laenge: 300,
        breite: 200,
        hoehe: 18,
        material_id: "buche_massiv",
        nullpunkt: [0, 0, 0],
        z_referenz: "material_top",
      },
      setups,
      notizen: "",
    };
  }

  async function pruefen() {
    setFehler(null);
    try {
      const b = await camwosaApi.workflowPruefen(varianteFuerBackend());
      setPruefBericht(b);
    } catch (e: unknown) {
      setFehler(e instanceof Error ? e.message : String(e));
    }
  }

  async function arbeitsplanMd() {
    if (!maschine) {
      setFehler("Bitte Maschine im Projekt waehlen.");
      return;
    }
    setFehler(null);
    try {
      const r = await camwosaApi.workflowArbeitsplanMd(
        varianteFuerBackend(),
        projektName,
        maschine.id,
      );
      setMarkdown(r.markdown);
    } catch (e: unknown) {
      setFehler(e instanceof Error ? e.message : String(e));
    }
  }

  async function arbeitsplanPdf() {
    if (!maschine) {
      setFehler("Bitte Maschine im Projekt waehlen.");
      return;
    }
    setFehler(null);
    try {
      const blob = await camwosaApi.workflowArbeitsplanPdf(
        varianteFuerBackend(),
        projektName,
        maschine.id,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `arbeitsplan_${projektName}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      setFehler(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("navigation.workflow")}</h1>
        <div className="flex items-center gap-2">
          <input
            className="rounded bg-camwosa-bg px-2 py-1 text-sm"
            value={projektName}
            onChange={(e) => setProjektName(e.target.value)}
            placeholder="Projekt-Name"
          />
          <button
            className="rounded border border-gray-600 px-3 py-1 text-xs"
            onClick={alleZuruecksetzen}
            title="Checkliste fuer neuen Lauf zuruecksetzen"
          >
            ↺ Checkliste
          </button>
          <button
            className="rounded border border-gray-600 px-3 py-1 text-xs"
            onClick={() => void pruefen()}
          >
            Pruefen
          </button>
          <button
            className="rounded border border-gray-600 px-3 py-1 text-xs"
            onClick={() => void arbeitsplanMd()}
          >
            Arbeitsplan
          </button>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white"
            onClick={() => void arbeitsplanPdf()}
          >
            PDF herunterladen
          </button>
        </div>
      </div>

      {fehler && (
        <div className="rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
          {fehler}
        </div>
      )}

      {pruefBericht && (
        <div
          className={clsx(
            "rounded border p-3 text-sm",
            pruefBericht.hat_blocker
              ? "border-camwosa-danger bg-red-950/30"
              : "border-camwosa-ok bg-green-950/20",
          )}
        >
          <strong>
            {pruefBericht.hat_blocker ? "Probleme im Workflow!" : "Workflow OK"}
          </strong>
          {pruefBericht.probleme.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs">
              {pruefBericht.probleme.map((p, i) => (
                <li key={i}>
                  <span className="font-semibold">[{p.stufe}]</span> {p.text}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <section className="rounded border border-gray-700 bg-camwosa-surface">
        <header className="flex items-center justify-between border-b border-gray-700 px-3 py-2">
          <h2 className="text-sm font-semibold">Setups ({setups.length})</h2>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
            onClick={neuesSetupAnlegen}
            disabled={werkzeuge.length === 0}
          >
            + Setup hinzufuegen
          </button>
        </header>
        {setups.length === 0 && (
          <p className="p-4 text-sm text-camwosa-muted">
            Noch keine Setups. „Setup hinzufuegen" klicken um anzulegen.
          </p>
        )}
        <ol className="divide-y divide-gray-800">
          {setups.map((s, idx) => (
            <li key={s.id} className="p-3">
              {s.pause_vor && (
                <PauseEditor
                  pause={s.pause_vor}
                  erledigt={!!erledigt[`${s.id}:pause`]}
                  onToggleErledigt={() => toggleErledigt(`${s.id}:pause`)}
                  onChange={(p) => pauseSetzen(s.id, p)}
                  onRemove={() => pauseSetzen(s.id, null)}
                />
              )}
              {!s.pause_vor && idx > 0 && (
                <button
                  className="mb-2 rounded border border-dashed border-gray-600 px-3 py-1 text-xs text-camwosa-muted hover:bg-gray-700"
                  onClick={() =>
                    pauseSetzen(s.id, {
                      typ: "werkzeugwechsel",
                      titel: "Werkzeugwechsel",
                      anweisung: "",
                    })
                  }
                >
                  + Pause vor diesem Setup
                </button>
              )}
              <SetupEditor
                setup={s}
                werkzeuge={werkzeuge}
                erledigt={!!erledigt[s.id]}
                onToggleErledigt={() => toggleErledigt(s.id)}
                onChange={(patch) => aktualisieren(s.id, patch)}
                onMoveUp={idx > 0 ? () => verschieben(s.id, -1) : undefined}
                onMoveDown={
                  idx < setups.length - 1 ? () => verschieben(s.id, 1) : undefined
                }
                onDelete={() => loeschen(s.id)}
              />
            </li>
          ))}
        </ol>
      </section>

      {markdown && (
        <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
          <h2 className="mb-2 text-sm font-semibold">Arbeitsplan</h2>
          <pre className="max-h-[40vh] overflow-auto rounded bg-camwosa-bg p-3 text-xs">
            {markdown}
          </pre>
        </section>
      )}
    </div>
  );
}

function SetupEditor({
  setup,
  werkzeuge,
  erledigt,
  onToggleErledigt,
  onChange,
  onMoveUp,
  onMoveDown,
  onDelete,
}: {
  setup: Setup;
  werkzeuge: Array<{ id: string; name: string }>;
  erledigt: boolean;
  onToggleErledigt: () => void;
  onChange: (patch: Partial<Setup>) => void;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  onDelete: () => void;
}) {
  return (
    <div
      className={
        erledigt
          ? "rounded border border-camwosa-ok bg-green-950/10 p-3 opacity-70"
          : "rounded border border-gray-700 bg-camwosa-bg p-3"
      }
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            className={
              erledigt
                ? "h-5 w-5 rounded border border-camwosa-ok bg-camwosa-ok text-white"
                : "h-5 w-5 rounded border border-gray-500 hover:border-camwosa-accent"
            }
            onClick={onToggleErledigt}
            title="Als erledigt markieren"
          >
            {erledigt ? "✓" : ""}
          </button>
          <input
            className={
              erledigt
                ? "rounded bg-camwosa-surface px-2 py-1 text-sm font-medium line-through"
                : "rounded bg-camwosa-surface px-2 py-1 text-sm font-medium"
            }
            value={setup.name}
            onChange={(e) => onChange({ name: e.target.value })}
          />
        </div>
        <div className="flex gap-1">
          <button
            className="rounded border border-gray-600 px-2 py-0.5 text-xs disabled:opacity-30"
            onClick={onMoveUp}
            disabled={!onMoveUp}
          >
            ↑
          </button>
          <button
            className="rounded border border-gray-600 px-2 py-0.5 text-xs disabled:opacity-30"
            onClick={onMoveDown}
            disabled={!onMoveDown}
          >
            ↓
          </button>
          <button
            className="rounded border border-gray-600 px-2 py-0.5 text-xs text-camwosa-muted hover:text-camwosa-danger"
            onClick={onDelete}
          >
            Loeschen
          </button>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <label>
          <span className="text-camwosa-muted">Modus</span>
          <select
            className="mt-0.5 w-full rounded bg-camwosa-surface px-2 py-1"
            value={setup.maschinen_modus}
            onChange={(e) =>
              onChange({ maschinen_modus: e.target.value as Setup["maschinen_modus"] })
            }
          >
            <option value="standard_xyz">Standard XYZ</option>
            <option value="rotary_y">Rotary Y</option>
            <option value="rotary_x">Rotary X</option>
            <option value="laser">Laser</option>
            <option value="drag_knife">Drag Knife</option>
          </select>
        </label>
        <label>
          <span className="text-camwosa-muted">Werkzeug</span>
          <select
            className="mt-0.5 w-full rounded bg-camwosa-surface px-2 py-1"
            value={setup.werkzeug_id}
            onChange={(e) => onChange({ werkzeug_id: e.target.value })}
          >
            {werkzeuge.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="text-camwosa-muted">Zeit (min)</span>
          <input
            type="number"
            className="mt-0.5 w-full rounded bg-camwosa-surface px-2 py-1"
            value={setup.geschaetzte_zeit_minuten}
            onChange={(e) =>
              onChange({ geschaetzte_zeit_minuten: parseFloat(e.target.value) || 0 })
            }
          />
        </label>
        <label className="col-span-3">
          <span className="text-camwosa-muted">Spannmittel</span>
          <input
            className="mt-0.5 w-full rounded bg-camwosa-surface px-2 py-1"
            value={setup.spannmittel}
            onChange={(e) => onChange({ spannmittel: e.target.value })}
            placeholder="z.B. Schraubzwingen x 4, Backen + Reitstock"
          />
        </label>
        <label className="col-span-3">
          <span className="text-camwosa-muted">Notizen</span>
          <textarea
            className="mt-0.5 w-full rounded bg-camwosa-surface px-2 py-1"
            rows={2}
            value={setup.notizen}
            onChange={(e) => onChange({ notizen: e.target.value })}
          />
        </label>
      </div>
      <div className="mt-2">
        <FotoSlot
          fotoPfad={setup.foto_pfad}
          onChange={(p) => onChange({ foto_pfad: p })}
        />
      </div>
    </div>
  );
}

function PauseEditor({
  pause,
  erledigt,
  onToggleErledigt,
  onChange,
  onRemove,
}: {
  pause: SetupPause;
  erledigt: boolean;
  onToggleErledigt: () => void;
  onChange: (p: SetupPause) => void;
  onRemove: () => void;
}) {
  return (
    <div
      className={
        erledigt
          ? "mb-2 rounded border border-camwosa-ok bg-green-950/10 p-3 opacity-70"
          : "mb-2 rounded border border-camwosa-warn bg-yellow-950/20 p-3"
      }
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-camwosa-warn">
          <button
            className={
              erledigt
                ? "h-4 w-4 rounded border border-camwosa-ok bg-camwosa-ok text-white"
                : "h-4 w-4 rounded border border-gray-500 hover:border-camwosa-accent"
            }
            onClick={onToggleErledigt}
          >
            {erledigt ? "✓" : ""}
          </button>
          🔧 PAUSE
          <select
            className="rounded bg-camwosa-bg px-2 py-0.5"
            value={pause.typ}
            onChange={(e) =>
              onChange({ ...pause, typ: e.target.value as SetupPauseTyp })
            }
          >
            <option value="werkzeugwechsel">{PAUSE_LABEL.werkzeugwechsel}</option>
            <option value="umspann">{PAUSE_LABEL.umspann}</option>
            <option value="werkstueck_verschieben">{PAUSE_LABEL.werkstueck_verschieben}</option>
            <option value="spindel_wechsel">{PAUSE_LABEL.spindel_wechsel}</option>
            <option value="optionaler_stop">{PAUSE_LABEL.optionaler_stop}</option>
          </select>
        </div>
        <button
          className="rounded border border-gray-600 px-2 py-0.5 text-xs text-camwosa-muted hover:text-camwosa-danger"
          onClick={onRemove}
        >
          Entfernen
        </button>
      </div>
      <input
        className="mb-1 w-full rounded bg-camwosa-bg px-2 py-1 text-xs"
        value={pause.titel}
        onChange={(e) => onChange({ ...pause, titel: e.target.value })}
        placeholder="Titel"
      />
      <textarea
        className="w-full rounded bg-camwosa-bg px-2 py-1 text-xs"
        rows={3}
        value={pause.anweisung}
        onChange={(e) => onChange({ ...pause, anweisung: e.target.value })}
        placeholder="Anweisungen fuer den Bediener (Multi-line)"
      />
    </div>
  );
}
