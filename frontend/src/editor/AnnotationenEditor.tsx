import { useState } from "react";
import { camwosaApi } from "../api/client";

export type AnnotationTyp = "anschlagbohrung" | "refpunkt" | "kommentar" | "ausschnitt";

export interface Annotation {
  id: string;
  typ: AnnotationTyp;
  x: number;
  y: number;
  z?: number;
  durchmesser_mm?: number | null;
  tiefe_mm?: number | null;
  text?: string;
}

const TYP_LABEL: Record<AnnotationTyp, string> = {
  anschlagbohrung: "Anschlagbohrung",
  refpunkt: "Refpunkt",
  kommentar: "Kommentar",
  ausschnitt: "Ausschnitt",
};

const TYP_ICON: Record<AnnotationTyp, string> = {
  anschlagbohrung: "⊙",
  refpunkt: "✜",
  kommentar: "💬",
  ausschnitt: "▢",
};

interface GeneratedOp {
  id: string;
  name: string;
  typ: string;
  parameter: Record<string, unknown>;
}

interface Props {
  annotationen: Annotation[];
  onChange: (a: Annotation[]) => void;
  /** Optional: Aufruf bei Klick auf "Position setzen" — der Caller hat den 2D-Viewer
   *  und kann den User per Klick im Canvas Koordinaten eingeben lassen. */
  onPosWaehlen?: (id: string) => void;
  /** Optional: wenn gesetzt, kommt ein „→ Operationen erzeugen"-Button.
   *  Der Caller bekommt die generierten Operationen + Hinweise und entscheidet
   *  was er damit macht (z.B. in den App-Store legen). */
  onOperationenErzeugt?: (ops: GeneratedOp[], hinweise: string[]) => void;
}

/**
 * Editor fuer Geometrie-Annotationen — Anschlagbohrungen, Refpunkte, Kommentare,
 * Ausschnitte. Mutiert NICHT die Original-Geometrie. Wird vom Workflow-Modul
 * spaeter automatisch in Bohren-Operationen / Tasche-Operationen umgesetzt.
 */
export default function AnnotationenEditor({
  annotationen, onChange, onPosWaehlen, onOperationenErzeugt,
}: Props) {
  const [busy, setBusy] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  async function erzeuge_operationen() {
    if (!onOperationenErzeugt) return;
    setBusy(true); setFehler(null);
    try {
      const r = await camwosaApi.annotationenZuOperationen(
        annotationen.map((a) => ({ ...a })),
      );
      onOperationenErzeugt(r.operationen, r.hinweise);
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Fehler beim Erzeugen");
    } finally {
      setBusy(false);
    }
  }

  function add(typ: AnnotationTyp) {
    const id = `a_${Date.now().toString(36)}`;
    const neu: Annotation = {
      id, typ, x: 0, y: 0, z: 0,
      ...(typ === "anschlagbohrung" || typ === "ausschnitt"
        ? { durchmesser_mm: 3, tiefe_mm: typ === "anschlagbohrung" ? 8 : 2 }
        : {}),
      text: typ === "kommentar" ? "Hinweis" : "",
    };
    onChange([...annotationen, neu]);
  }

  function update(id: string, patch: Partial<Annotation>) {
    onChange(annotationen.map((a) => (a.id === id ? { ...a, ...patch } : a)));
  }

  function loeschen(id: string) {
    onChange(annotationen.filter((a) => a.id !== id));
  }

  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-camwosa-muted">Annotation hinzufuegen:</span>
        {(Object.keys(TYP_LABEL) as AnnotationTyp[]).map((t) => (
          <button
            key={t}
            className="rounded border border-gray-600 px-2 py-1 text-xs hover:bg-camwosa-overlay"
            onClick={() => add(t)}
          >
            <span className="mr-1">{TYP_ICON[t]}</span>+ {TYP_LABEL[t]}
          </button>
        ))}
      </div>

      {onOperationenErzeugt && annotationen.length > 0 && (
        <div className="flex items-center justify-between rounded border border-camwosa-accent/40 bg-camwosa-accent-soft p-2">
          <span className="text-xs text-camwosa-text">
            ⚙ {annotationen.length} Annotation(en) → CAM-Operationen erzeugen.
            Bohrungen werden nach Tiefe + Ø gruppiert.
          </span>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-medium text-camwosa-bg hover:opacity-90 disabled:opacity-50"
            disabled={busy}
            onClick={() => void erzeuge_operationen()}
          >
            {busy ? "..." : "→ Operationen erzeugen"}
          </button>
        </div>
      )}

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
          {fehler}
        </div>
      )}

      <ul className="space-y-2">
        {annotationen.length === 0 && (
          <li className="rounded border border-dashed border-gray-700 p-3 text-center text-xs text-camwosa-muted">
            Keine Annotationen. Beispiel: 4 Anschlagbohrungen an die Ecken setzen
            — werden im Workflow automatisch als Bohren-Operation generiert.
          </li>
        )}
        {annotationen.map((a) => (
          <li key={a.id} className="rounded border border-gray-700 bg-camwosa-surface p-2">
            <div className="mb-2 flex items-center gap-2">
              <span className="w-6 text-center text-base">{TYP_ICON[a.typ]}</span>
              <span className="flex-1 text-xs">
                <strong>{TYP_LABEL[a.typ]}</strong>{" "}
                <span className="font-mono text-camwosa-muted">
                  ({a.x.toFixed(1)}, {a.y.toFixed(1)}, {a.z?.toFixed(1) ?? "0.0"})
                </span>
              </span>
              {onPosWaehlen && (
                <button
                  className="rounded border border-gray-600 px-2 py-0.5 text-xs hover:bg-camwosa-overlay"
                  onClick={() => onPosWaehlen(a.id)}
                  title="Position im 2D-Viewer per Klick setzen"
                >
                  ↗ Klicken
                </button>
              )}
              <button
                className="rounded border border-red-700 px-2 py-0.5 text-xs hover:bg-red-900/40"
                onClick={() => loeschen(a.id)}
              >
                🗑
              </button>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs">
              <Num label="X (mm)" v={a.x} on={(v) => update(a.id, { x: v ?? 0 })} step={0.1} />
              <Num label="Y (mm)" v={a.y} on={(v) => update(a.id, { y: v ?? 0 })} step={0.1} />
              <Num label="Z (mm)" v={a.z ?? 0} on={(v) => update(a.id, { z: v ?? 0 })} step={0.1} />

              {(a.typ === "anschlagbohrung" || a.typ === "ausschnitt") && (
                <>
                  <Num
                    label="Ø (mm)"
                    v={a.durchmesser_mm ?? null}
                    on={(v) => update(a.id, { durchmesser_mm: v })}
                    step={0.1}
                  />
                  <Num
                    label="Tiefe (mm)"
                    v={a.tiefe_mm ?? null}
                    on={(v) => update(a.id, { tiefe_mm: v })}
                    step={0.5}
                  />
                </>
              )}

              {(a.typ === "kommentar" || a.text !== undefined) && (
                <label className="col-span-3 text-xs">
                  <span className="mb-0.5 block text-camwosa-muted">Text</span>
                  <input
                    className="w-full rounded bg-camwosa-bg px-2 py-1"
                    value={a.text ?? ""}
                    onChange={(e) => update(a.id, { text: e.target.value })}
                  />
                </label>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Num({
  label, v, on, step,
}: { label: string; v: number | null; on: (v: number | null) => void; step: number }) {
  return (
    <label className="text-xs">
      <span className="mb-0.5 block text-camwosa-muted">{label}</span>
      <input
        type="number"
        step={step}
        value={v ?? ""}
        onChange={(e) => on(e.target.value === "" ? null : Number(e.target.value))}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
    </label>
  );
}
