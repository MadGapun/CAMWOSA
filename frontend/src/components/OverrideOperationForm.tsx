/**
 * Override-aware OperationForm.
 *
 * Im Gegensatz zum klassischen OperationForm sind alle Felder optional:
 * null = Standard (aus Material-Preset / Projekt-Default) wird verwendet.
 * Pro Feld kann der Nutzer einen Override setzen und wieder zuruecksetzen.
 *
 * Die Komponente fragt das Backend periodisch nach den aufgeloesten Werten +
 * Quellen — so wird angezeigt woher der Standard kommt (Material-Preset?
 * Projekt-Default? Fallback?).
 */

import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import OverrideField from "./OverrideField";
import type { OperationsTyp } from "../api/types";

interface Props {
  typ: OperationsTyp;
  werkzeugId: string;
  materialId: string | null;
  /** Aktuelle Overrides (alle Felder optional). */
  overrides: Record<string, unknown>;
  onChange: (overrides: Record<string, unknown>) => void;
}

interface Aufloesung {
  parameter: Record<string, unknown>;
  quellen: Record<string, string>;
}

type QuelleTyp = "override" | "material_preset" | "projekt_default" | "fallback" | "werkzeug";

export default function OverrideOperationForm({
  typ, werkzeugId, materialId, overrides, onChange,
}: Props) {
  const [aufloesung, setAufloesung] = useState<Aufloesung | null>(null);

  // Bei Aenderungen erneut auflosen
  useEffect(() => {
    if (!materialId || !werkzeugId) return;
    let cancel = false;
    (async () => {
      try {
        const r = await camwosaApi.opAufloesen(
          typ as "kontur" | "tasche" | "bohren" | "gravur",
          materialId,
          { ...overrides, werkzeug_id: werkzeugId },
        );
        if (!cancel) setAufloesung(r);
      } catch {
        // Fehler still ignorieren — Werte einfach nicht anzeigen
      }
    })();
    return () => {
      cancel = true;
    };
  }, [typ, werkzeugId, materialId, JSON.stringify(overrides)]);

  function set(feld: string, wert: unknown) {
    const next = { ...overrides };
    if (wert === null || wert === undefined || wert === "") {
      delete next[feld];
    } else {
      next[feld] = wert;
    }
    onChange(next);
  }

  function ov<T = number>(feld: string): T | null {
    const v = overrides[feld];
    return (v === undefined ? null : (v as T));
  }

  function eff(feld: string): unknown {
    return aufloesung?.parameter[feld];
  }

  function quelle(feld: string): QuelleTyp {
    return (aufloesung?.quellen[feld] as QuelleTyp) ?? "fallback";
  }

  if (!materialId) {
    return (
      <div className="rounded border border-camwosa-warn bg-yellow-950/20 p-2 text-xs text-camwosa-warn">
        Bitte zuerst ein Material im Projekt waehlen — sonst koennen keine
        Standardwerte aufgeloest werden.
      </div>
    );
  }

  // Gemeinsame Felder fuer alle Operations-Typen
  const Basis = (
    <>
      <OverrideField
        label="Spindel-RPM" einheit="U/min" step={500}
        wert={ov<number>("spindel_rpm")}
        onChange={(v) => set("spindel_rpm", v)}
        onReset={() => set("spindel_rpm", null)}
        quelle={quelle("spindel_rpm")}
        effektivAnzeige={eff("spindel_rpm") as number}
      />
      <OverrideField
        label="Vorschub" einheit="mm/min" step={100}
        wert={ov<number>("vorschub")}
        onChange={(v) => set("vorschub", v)}
        onReset={() => set("vorschub", null)}
        quelle={quelle("vorschub")}
        effektivAnzeige={eff("vorschub") as number}
      />
      <OverrideField
        label="Eintauchvorschub" einheit="mm/min" step={50}
        wert={ov<number>("eintauch_vorschub")}
        onChange={(v) => set("eintauch_vorschub", v)}
        onReset={() => set("eintauch_vorschub", null)}
        quelle={quelle("eintauch_vorschub")}
        effektivAnzeige={eff("eintauch_vorschub") as number}
      />
      <OverrideField
        label="Sicherheitshoehe" einheit="mm" step={0.5}
        wert={ov<number>("sicherheitshoehe")}
        onChange={(v) => set("sicherheitshoehe", v)}
        onReset={() => set("sicherheitshoehe", null)}
        quelle={quelle("sicherheitshoehe")}
        effektivAnzeige={eff("sicherheitshoehe") as number}
      />
      <OverrideField
        label="Max. Tiefe" einheit="mm" step={0.5} min={0.1}
        wert={ov<number>("max_tiefe")}
        onChange={(v) => set("max_tiefe", v)}
        onReset={() => set("max_tiefe", null)}
        quelle={quelle("max_tiefe")}
        effektivAnzeige={eff("max_tiefe") as number}
      />
      <OverrideField
        label="Stepdown" einheit="mm" step={0.1} min={0.1}
        wert={ov<number>("stepdown")}
        onChange={(v) => set("stepdown", v)}
        onReset={() => set("stepdown", null)}
        quelle={quelle("stepdown")}
        effektivAnzeige={eff("stepdown") as number}
      />
    </>
  );

  if (typ === "kontur") {
    return (
      <div className="grid grid-cols-3 gap-2">
        {Basis}
        <OverrideField<"innen" | "aussen" | "auf_linie">
          typ="select" label="Seite"
          wert={ov<"innen" | "aussen" | "auf_linie">("seite")}
          onChange={(v) => set("seite", v)}
          onReset={() => set("seite", null)}
          quelle={quelle("seite")}
          effektivAnzeige={eff("seite") as string}
          options={[
            { value: "aussen", label: "Aussen" },
            { value: "innen", label: "Innen" },
            { value: "auf_linie", label: "Auf Linie" },
          ]}
        />
        <OverrideField<"gleichlauf" | "gegenlauf">
          typ="select" label="Fraesrichtung"
          wert={ov<"gleichlauf" | "gegenlauf">("fraes_richtung")}
          onChange={(v) => set("fraes_richtung", v)}
          onReset={() => set("fraes_richtung", null)}
          quelle={quelle("fraes_richtung")}
          effektivAnzeige={eff("fraes_richtung") as string}
          options={[
            { value: "gleichlauf", label: "Gleichlauf (Climb)" },
            { value: "gegenlauf", label: "Gegenlauf (Conventional)" },
          ]}
        />
        <OverrideField<"rampe" | "helix" | "senkrecht">
          typ="select" label="Eintauchstrategie"
          wert={ov<"rampe" | "helix" | "senkrecht">("eintauch_strategie")}
          onChange={(v) => set("eintauch_strategie", v)}
          onReset={() => set("eintauch_strategie", null)}
          quelle={quelle("eintauch_strategie")}
          effektivAnzeige={eff("eintauch_strategie") as string}
          options={[
            { value: "rampe", label: "Rampe" },
            { value: "helix", label: "Helix" },
            { value: "senkrecht", label: "Senkrecht" },
          ]}
        />
        <OverrideField label="Tabs Anzahl" step={1} min={0}
          wert={ov<number>("tabs_anzahl")}
          onChange={(v) => set("tabs_anzahl", v)}
          onReset={() => set("tabs_anzahl", null)}
          quelle={quelle("tabs_anzahl")}
          effektivAnzeige={eff("tabs_anzahl") as number}
        />
        <OverrideField label="Tabs Hoehe" einheit="mm" step={0.1}
          wert={ov<number>("tabs_hoehe")}
          onChange={(v) => set("tabs_hoehe", v)}
          onReset={() => set("tabs_hoehe", null)}
          quelle={quelle("tabs_hoehe")}
          effektivAnzeige={eff("tabs_hoehe") as number}
        />
        <OverrideField label="Tabs Breite" einheit="mm" step={0.5}
          wert={ov<number>("tabs_breite")}
          onChange={(v) => set("tabs_breite", v)}
          onReset={() => set("tabs_breite", null)}
          quelle={quelle("tabs_breite")}
          effektivAnzeige={eff("tabs_breite") as number}
        />
        <OverrideField label="Aufmass" einheit="mm" step={0.1}
          wert={ov<number>("aufmass")}
          onChange={(v) => set("aufmass", v)}
          onReset={() => set("aufmass", null)}
          quelle={quelle("aufmass")}
          effektivAnzeige={eff("aufmass") as number}
        />
      </div>
    );
  }

  if (typ === "tasche") {
    return (
      <div className="grid grid-cols-3 gap-2">
        {Basis}
        <OverrideField<"parallel" | "offset_kontur" | "spiral_aussen" | "spiral_innen" | "adaptive">
          typ="select" label="Strategie"
          wert={ov("strategie")}
          onChange={(v) => set("strategie", v)}
          onReset={() => set("strategie", null)}
          quelle={quelle("strategie")}
          effektivAnzeige={eff("strategie") as string}
          options={[
            { value: "parallel", label: "Parallel (Zickzack)" },
            { value: "offset_kontur", label: "Offset-Kontur" },
            { value: "spiral_aussen", label: "Spiral aussen (geplant)" },
            { value: "spiral_innen", label: "Spiral innen (geplant)" },
            { value: "adaptive", label: "Adaptive (geplant)" },
          ]}
        />
        <OverrideField label="Stepover" einheit="%" step={5} min={5} max={95}
          wert={ov<number>("stepover_prozent")}
          onChange={(v) => set("stepover_prozent", v)}
          onReset={() => set("stepover_prozent", null)}
          quelle={quelle("stepover_prozent")}
          effektivAnzeige={eff("stepover_prozent") as number}
        />
        <OverrideField<"rampe" | "helix" | "senkrecht">
          typ="select" label="Eintauchstrategie"
          wert={ov("eintauch_strategie")}
          onChange={(v) => set("eintauch_strategie", v)}
          onReset={() => set("eintauch_strategie", null)}
          quelle={quelle("eintauch_strategie")}
          effektivAnzeige={eff("eintauch_strategie") as string}
          options={[
            { value: "helix", label: "Helix" },
            { value: "rampe", label: "Rampe" },
            { value: "senkrecht", label: "Senkrecht" },
          ]}
        />
        <OverrideField label="Aufmass Wand" einheit="mm" step={0.1}
          wert={ov<number>("aufmass_wand")}
          onChange={(v) => set("aufmass_wand", v)}
          onReset={() => set("aufmass_wand", null)}
          quelle={quelle("aufmass_wand")}
          effektivAnzeige={eff("aufmass_wand") as number}
        />
        <OverrideField label="Aufmass Boden" einheit="mm" step={0.1}
          wert={ov<number>("aufmass_boden")}
          onChange={(v) => set("aufmass_boden", v)}
          onReset={() => set("aufmass_boden", null)}
          quelle={quelle("aufmass_boden")}
          effektivAnzeige={eff("aufmass_boden") as number}
        />
      </div>
    );
  }

  if (typ === "bohren") {
    return (
      <div className="grid grid-cols-3 gap-2">
        {Basis}
        <OverrideField<"standard" | "peck" | "tief_peck" | "helix" | "reib">
          typ="select" label="Strategie"
          wert={ov("strategie")}
          onChange={(v) => set("strategie", v)}
          onReset={() => set("strategie", null)}
          quelle={quelle("strategie")}
          effektivAnzeige={eff("strategie") as string}
          options={[
            { value: "standard", label: "Standard" },
            { value: "peck", label: "Peck (Spanbrechen)" },
            { value: "tief_peck", label: "Tief-Peck" },
            { value: "helix", label: "Helix (geplant)" },
            { value: "reib", label: "Reib (geplant)" },
          ]}
        />
        <OverrideField label="Peck-Tiefe" einheit="mm" step={0.5}
          wert={ov<number>("peck_tiefe")}
          onChange={(v) => set("peck_tiefe", v)}
          onReset={() => set("peck_tiefe", null)}
          quelle={quelle("peck_tiefe")}
          effektivAnzeige={eff("peck_tiefe") as number}
        />
        <OverrideField label="Dwell" einheit="s" step={0.1}
          wert={ov<number>("dwell_sekunden")}
          onChange={(v) => set("dwell_sekunden", v)}
          onReset={() => set("dwell_sekunden", null)}
          quelle={quelle("dwell_sekunden")}
          effektivAnzeige={eff("dwell_sekunden") as number}
        />
        <OverrideField label="Rueckzugshoehe" einheit="mm" step={0.5}
          wert={ov<number>("rueckzugs_hoehe")}
          onChange={(v) => set("rueckzugs_hoehe", v)}
          onReset={() => set("rueckzugs_hoehe", null)}
          quelle={quelle("rueckzugs_hoehe")}
          effektivAnzeige={eff("rueckzugs_hoehe") as number}
        />
      </div>
    );
  }

  if (typ === "gravur") {
    return (
      <div className="grid grid-cols-3 gap-2">
        {Basis}
        <OverrideField<"konstante_tiefe" | "v_carving">
          typ="select" label="Strategie"
          wert={ov("strategie")}
          onChange={(v) => set("strategie", v)}
          onReset={() => set("strategie", null)}
          quelle={quelle("strategie")}
          effektivAnzeige={eff("strategie") as string}
          options={[
            { value: "konstante_tiefe", label: "Konstante Tiefe" },
            { value: "v_carving", label: "V-Carving (geplant)" },
          ]}
        />
        <OverrideField label="Spitzenwinkel" einheit="°" step={1}
          wert={ov<number>("spitzenwinkel_grad")}
          onChange={(v) => set("spitzenwinkel_grad", v)}
          onReset={() => set("spitzenwinkel_grad", null)}
          quelle={quelle("spitzenwinkel_grad")}
          effektivAnzeige={eff("spitzenwinkel_grad") as number}
        />
        <OverrideField label="Max. Zustellung" einheit="mm" step={0.1}
          wert={ov<number>("max_zustellung")}
          onChange={(v) => set("max_zustellung", v)}
          onReset={() => set("max_zustellung", null)}
          quelle={quelle("max_zustellung")}
          effektivAnzeige={eff("max_zustellung") as number}
        />
      </div>
    );
  }

  return null;
}
