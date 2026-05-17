import clsx from "clsx";
import { FachTooltip } from "./Tooltip";
import { FACHBEGRIFFE } from "./fachbegriffe";

type QuelleTyp = "override" | "material_preset" | "projekt_default" | "fallback" | "werkzeug";

interface BaseProps {
  label: string;
  einheit?: string;
  quelle?: QuelleTyp;
  /** Effektiv aufgeloeste Anzeige (wenn Override null ist) */
  effektivAnzeige?: string | number;
  onReset?: () => void;
  disabled?: boolean;
  /** Wenn gesetzt, zeigt ein „?"-Icon neben dem Label mit einer Fachbegriff-Erklaerung.
   *  Wert muss ein Key aus ``FACHBEGRIFFE`` sein (siehe components/fachbegriffe.ts). */
  hilfe?: keyof typeof FACHBEGRIFFE;
}

interface NumProps extends BaseProps {
  typ?: "number";
  wert: number | null | undefined;
  onChange: (v: number | null) => void;
  step?: number;
  min?: number;
  max?: number;
}

interface SelectProps<T extends string> extends BaseProps {
  typ: "select";
  wert: T | null | undefined;
  onChange: (v: T | null) => void;
  options: { value: T; label: string }[];
}

interface CheckProps extends BaseProps {
  typ: "checkbox";
  wert: boolean | null | undefined;
  onChange: (v: boolean | null) => void;
}

type Props<T extends string = string> = NumProps | SelectProps<T> | CheckProps;

const QUELLE_LABEL: Record<QuelleTyp, string> = {
  override: "übersteuert",
  material_preset: "Material-Preset",
  projekt_default: "Projekt-Default",
  fallback: "Fallback",
  werkzeug: "Werkzeug",
};

const QUELLE_FARBE: Record<QuelleTyp, string> = {
  override: "text-camwosa-accent",
  material_preset: "text-camwosa-ok",
  projekt_default: "text-blue-400",
  fallback: "text-camwosa-muted",
  werkzeug: "text-purple-400",
};

/** 6px-Punkt-Klassen — siehe styles/index.css und Design-Note 2. */
const QUELLE_DOT_CLASS: Record<QuelleTyp, string> = {
  override: "override",
  material_preset: "material",
  projekt_default: "projekt",
  fallback: "fallback",
  werkzeug: "werkzeug",
};

/**
 * OverrideField: Ein Eingabefeld mit Override-Mechanik.
 *
 * - Wenn `wert === null/undefined` => Standard aktiv:
 *   - Anzeige der effektiven Quelle (Material-Preset / Projekt-Default / ...)
 *   - Wert grau, nicht editierbar
 *   - Klick darauf macht Override auf (Wert wird kopiert, editierbar)
 * - Wenn `wert !== null` => Override aktiv:
 *   - Normal editierbar
 *   - „↺ Reset"-Button setzt zurueck auf Standard (= wert wird null)
 */
export default function OverrideField<T extends string = string>(
  props: Props<T>,
) {
  const istOverride = props.wert !== null && props.wert !== undefined;
  const quelle = istOverride ? "override" : props.quelle ?? "fallback";

  return (
    <div className="rounded border border-gray-700 bg-camwosa-bg/40 p-2 text-xs">
      <div className="mb-1 flex items-center justify-between">
        <span className="flex items-center text-camwosa-muted">
          <span
            className={clsx("cw-src-dot", QUELLE_DOT_CLASS[quelle])}
            title={QUELLE_LABEL[quelle]}
          />
          {props.label}
          {props.einheit && (
            <span className="ml-1 text-[10px]">({props.einheit})</span>
          )}
          {props.hilfe && <FachTooltip {...FACHBEGRIFFE[props.hilfe]} />}
        </span>
        <span className="flex items-center gap-1.5">
          <span className={clsx("text-[10px]", QUELLE_FARBE[quelle])}>
            {QUELLE_LABEL[quelle]}
          </span>
          {istOverride && props.onReset && (
            <button
              className="rounded px-1 text-[10px] text-camwosa-muted hover:bg-gray-700 hover:text-white"
              title="Auf Standard zuruecksetzen"
              onClick={props.onReset}
              disabled={props.disabled}
            >
              ↺
            </button>
          )}
        </span>
      </div>

      {renderInput(props, istOverride)}
    </div>
  );
}

function renderInput<T extends string>(props: Props<T>, istOverride: boolean) {
  const grau = !istOverride;
  if (props.typ === "select") {
    const p = props as SelectProps<T>;
    return (
      <select
        className={clsx(
          "w-full rounded bg-camwosa-bg px-2 py-1",
          grau && "text-camwosa-muted",
        )}
        value={(p.wert ?? "") as string}
        onChange={(e) => p.onChange((e.target.value || null) as T | null)}
        disabled={p.disabled}
      >
        {grau && (
          <option value="">{`Standard${p.effektivAnzeige ? `: ${p.effektivAnzeige}` : ""}`}</option>
        )}
        {p.options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    );
  }
  if (props.typ === "checkbox") {
    const p = props as CheckProps;
    return (
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={p.wert ?? false}
          onChange={(e) => p.onChange(e.target.checked)}
          disabled={p.disabled}
        />
        {!istOverride && p.effektivAnzeige !== undefined && (
          <span className="text-camwosa-muted">
            Standard: {String(p.effektivAnzeige)}
          </span>
        )}
      </div>
    );
  }
  // number
  const p = props as NumProps;
  if (!istOverride) {
    return (
      <div
        className="cursor-pointer rounded bg-camwosa-bg px-2 py-1 text-camwosa-muted hover:bg-gray-700"
        onClick={() => p.onChange(typeof p.effektivAnzeige === "number"
          ? p.effektivAnzeige
          : 0)}
        title="Klick fuer Override"
      >
        {p.effektivAnzeige ?? "—"}
      </div>
    );
  }
  return (
    <input
      type="number"
      className="w-full rounded bg-camwosa-bg px-2 py-1"
      value={p.wert ?? ""}
      step={p.step}
      min={p.min}
      max={p.max}
      onChange={(e) => {
        const v = e.target.value;
        p.onChange(v === "" ? null : parseFloat(v) || 0);
      }}
      disabled={p.disabled}
    />
  );
}
