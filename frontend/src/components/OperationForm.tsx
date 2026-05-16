import type {
  BohrParameter,
  BohrStrategie,
  Eintauchstrategie,
  FraesRichtung,
  GravurParameter,
  KonturParameter,
  KonturSeite,
  OperationsTyp,
  TaschenParameter,
  TaschenStrategie,
} from "../api/types";

interface Props {
  typ: OperationsTyp;
  parameter: Record<string, unknown>;
  onChange: (parameter: Record<string, unknown>) => void;
}

function NumField({
  label, value, onChange, step = 1, min, max, einheit,
}: {
  label: string; value: number; onChange: (n: number) => void;
  step?: number; min?: number; max?: number; einheit?: string;
}) {
  return (
    <label className="block text-xs">
      <span className="text-camwosa-muted">{label}{einheit ? ` (${einheit})` : ""}</span>
      <input
        type="number"
        className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      />
    </label>
  );
}

function SelectField<T extends string>({
  label, value, options, onChange,
}: {
  label: string; value: T; options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <label className="block text-xs">
      <span className="text-camwosa-muted">{label}</span>
      <select
        className="mt-0.5 w-full rounded bg-camwosa-bg px-2 py-1 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

function CheckField({
  label, value, onChange,
}: { label: string; value: boolean; onChange: (b: boolean) => void }) {
  return (
    <label className="flex items-center gap-2 text-xs">
      <input
        type="checkbox" checked={value}
        onChange={(e) => onChange(e.target.checked)}
      />
      {label}
    </label>
  );
}

export default function OperationForm({ typ, parameter, onChange }: Props) {
  const set = (patch: Record<string, unknown>) => onChange({ ...parameter, ...patch });

  // Gemeinsame Felder
  const Basis = (
    <>
      <NumField label="Spindel-RPM" value={parameter.spindel_rpm as number}
                onChange={(n) => set({ spindel_rpm: n })} step={500} einheit="U/min" />
      <NumField label="Vorschub" value={parameter.vorschub as number}
                onChange={(n) => set({ vorschub: n })} step={100} einheit="mm/min" />
      <NumField label="Eintauchvorschub" value={parameter.eintauch_vorschub as number}
                onChange={(n) => set({ eintauch_vorschub: n })} step={50} einheit="mm/min" />
      <NumField label="Sicherheitshoehe" value={parameter.sicherheitshoehe as number}
                onChange={(n) => set({ sicherheitshoehe: n })} step={0.5} einheit="mm" />
      <NumField label="Max. Tiefe" value={parameter.max_tiefe as number}
                onChange={(n) => set({ max_tiefe: n })} step={0.5} min={0.1} einheit="mm" />
      <NumField label="Stepdown" value={parameter.stepdown as number}
                onChange={(n) => set({ stepdown: n })} step={0.1} min={0.1} einheit="mm" />
    </>
  );

  if (typ === "kontur") {
    const p = parameter as unknown as KonturParameter;
    return (
      <div className="grid grid-cols-2 gap-3">
        {Basis}
        <SelectField<KonturSeite>
          label="Seite" value={p.seite}
          options={[
            { value: "aussen", label: "Aussen" },
            { value: "innen", label: "Innen" },
            { value: "auf_linie", label: "Auf Linie" },
          ]}
          onChange={(v) => set({ seite: v })}
        />
        <SelectField<FraesRichtung>
          label="Fraesrichtung" value={p.fraes_richtung}
          options={[
            { value: "gleichlauf", label: "Gleichlauf (Climb)" },
            { value: "gegenlauf", label: "Gegenlauf (Conventional)" },
          ]}
          onChange={(v) => set({ fraes_richtung: v })}
        />
        <SelectField<Eintauchstrategie>
          label="Eintauchstrategie" value={p.eintauch_strategie}
          options={[
            { value: "rampe", label: "Rampe" },
            { value: "helix", label: "Helix" },
            { value: "senkrecht", label: "Senkrecht" },
          ]}
          onChange={(v) => set({ eintauch_strategie: v })}
        />
        <NumField label="Rampe-Winkel" value={p.rampe_winkel_grad}
                  onChange={(n) => set({ rampe_winkel_grad: n })} step={1}
                  min={1} max={45} einheit="°" />
        <NumField label="Tabs Anzahl" value={p.tabs_anzahl}
                  onChange={(n) => set({ tabs_anzahl: n })} step={1} min={0} />
        <NumField label="Tabs Hoehe" value={p.tabs_hoehe}
                  onChange={(n) => set({ tabs_hoehe: n })} step={0.1} einheit="mm" />
        <NumField label="Tabs Breite" value={p.tabs_breite}
                  onChange={(n) => set({ tabs_breite: n })} step={0.5} einheit="mm" />
        <NumField label="Aufmass" value={p.aufmass}
                  onChange={(n) => set({ aufmass: n })} step={0.1} einheit="mm" />
        <NumField label="Lead-In" value={p.lead_in_laenge}
                  onChange={(n) => set({ lead_in_laenge: n })} step={0.5} einheit="mm" />
        <NumField label="Lead-Out" value={p.lead_out_laenge}
                  onChange={(n) => set({ lead_out_laenge: n })} step={0.5} einheit="mm" />
        <CheckField label="Schlichtgang" value={p.schlichtgang}
                    onChange={(b) => set({ schlichtgang: b })} />
      </div>
    );
  }

  if (typ === "tasche") {
    const p = parameter as unknown as TaschenParameter;
    return (
      <div className="grid grid-cols-2 gap-3">
        {Basis}
        <SelectField<TaschenStrategie>
          label="Strategie" value={p.strategie}
          options={[
            { value: "parallel", label: "Parallel (Zickzack)" },
            { value: "offset_kontur", label: "Offset-Kontur" },
            { value: "spiral_aussen", label: "Spiral aussen (geplant)" },
            { value: "spiral_innen", label: "Spiral innen (geplant)" },
            { value: "adaptive", label: "Adaptive (geplant)" },
          ]}
          onChange={(v) => set({ strategie: v })}
        />
        <NumField label="Stepover" value={p.stepover_prozent}
                  onChange={(n) => set({ stepover_prozent: n })} step={5}
                  min={5} max={95} einheit="%" />
        <SelectField<Eintauchstrategie>
          label="Eintauchstrategie" value={p.eintauch_strategie}
          options={[
            { value: "helix", label: "Helix" },
            { value: "rampe", label: "Rampe" },
            { value: "senkrecht", label: "Senkrecht" },
          ]}
          onChange={(v) => set({ eintauch_strategie: v })}
        />
        <NumField label="Aufmass Wand" value={p.aufmass_wand}
                  onChange={(n) => set({ aufmass_wand: n })} step={0.1} einheit="mm" />
        <NumField label="Aufmass Boden" value={p.aufmass_boden}
                  onChange={(n) => set({ aufmass_boden: n })} step={0.1} einheit="mm" />
        <CheckField label="Schlichtgang Wand" value={p.schlichtgang_wand}
                    onChange={(b) => set({ schlichtgang_wand: b })} />
        <CheckField label="Schlichtgang Boden" value={p.schlichtgang_boden}
                    onChange={(b) => set({ schlichtgang_boden: b })} />
      </div>
    );
  }

  if (typ === "bohren") {
    const p = parameter as unknown as BohrParameter;
    return (
      <div className="grid grid-cols-2 gap-3">
        {Basis}
        <SelectField<BohrStrategie>
          label="Strategie" value={p.strategie}
          options={[
            { value: "standard", label: "Standard" },
            { value: "peck", label: "Peck (Spanbrechen)" },
            { value: "tief_peck", label: "Tief-Peck" },
            { value: "helix", label: "Helix (geplant)" },
            { value: "reib", label: "Reib (geplant)" },
          ]}
          onChange={(v) => set({ strategie: v })}
        />
        <NumField label="Peck-Tiefe" value={p.peck_tiefe}
                  onChange={(n) => set({ peck_tiefe: n })} step={0.5} einheit="mm" />
        <NumField label="Dwell" value={p.dwell_sekunden}
                  onChange={(n) => set({ dwell_sekunden: n })} step={0.1} einheit="s" />
        <NumField label="Rueckzugshoehe" value={p.rueckzugs_hoehe}
                  onChange={(n) => set({ rueckzugs_hoehe: n })} step={0.5} einheit="mm" />
      </div>
    );
  }

  if (typ === "gravur") {
    const p = parameter as unknown as GravurParameter;
    return (
      <div className="grid grid-cols-2 gap-3">
        {Basis}
        <SelectField
          label="Strategie" value={p.strategie}
          options={[
            { value: "konstante_tiefe", label: "Konstante Tiefe" },
            { value: "v_carving", label: "V-Carving (geplant)" },
          ]}
          onChange={(v) => set({ strategie: v })}
        />
        <NumField label="Spitzenwinkel" value={p.spitzenwinkel_grad ?? 60}
                  onChange={(n) => set({ spitzenwinkel_grad: n })} step={1} einheit="°" />
        <NumField label="Max. Zustellung" value={p.max_zustellung}
                  onChange={(n) => set({ max_zustellung: n })} step={0.1} einheit="mm" />
      </div>
    );
  }

  return <div>Unbekannter Operations-Typ: {typ}</div>;
}
