import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import type { FeedsSpeedsErgebnis } from "../api/types";
import clsx from "clsx";
import { FachTooltip } from "./Tooltip";
import { FACHBEGRIFFE } from "./fachbegriffe";

interface Props {
  maschineId: string | null;
  werkzeugId: string;
  materialId: string | null;
  rpmWunsch?: number;
}

export default function FeedsSpeedsPanel({
  maschineId, werkzeugId, materialId, rpmWunsch,
}: Props) {
  const [erg, setErg] = useState<FeedsSpeedsErgebnis | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!maschineId || !werkzeugId || !materialId) {
      setErg(null);
      return;
    }
    let cancel = false;
    (async () => {
      try {
        const r = await camwosaApi.feedsBerechnen(
          maschineId, werkzeugId, materialId, rpmWunsch,
        );
        if (!cancel) {
          setErg(r);
          setFehler(null);
        }
      } catch (e: unknown) {
        if (!cancel) setFehler(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => { cancel = true; };
  }, [maschineId, werkzeugId, materialId, rpmWunsch]);

  if (fehler) {
    return (
      <div className="rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
        Feeds&Speeds-Fehler: {fehler}
      </div>
    );
  }
  if (!maschineId || !materialId) {
    return (
      <div className="rounded border border-gray-700 bg-camwosa-surface p-3 text-xs text-camwosa-muted">
        Maschine + Material noetig fuer Feeds&Speeds-Berechnung
      </div>
    );
  }
  if (!erg) return null;

  return (
    <div className="rounded border border-gray-700 bg-camwosa-surface p-3">
      <h3 className="mb-2 text-sm font-semibold">
        Feeds & Speeds
        <span className="ml-2 text-xs font-normal text-camwosa-muted">
          (Quelle: {erg.quelle === "preset" ? "Material-Preset" : "Heuristik"})
        </span>
      </h3>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <Cell label="RPM" wert={erg.rpm.toFixed(0)} einheit="U/min" />
        <Cell label="Vorschub" wert={erg.vorschub.toFixed(0)} einheit="mm/min" hilfe="vorschub" />
        <Cell label="Eintauchvorschub" wert={erg.eintauch_vorschub.toFixed(0)} einheit="mm/min" hilfe="plunge" />
        <Cell label="Stepdown" wert={erg.stepdown.toFixed(2)} einheit="mm" hilfe="stepdown" />
        <Cell label="Stepover" wert={erg.stepover_prozent.toFixed(0)} einheit="%" hilfe="stepover" />
        <Cell label="Vc" wert={erg.schnittgeschwindigkeit_vc.toFixed(0)} einheit="m/min" hilfe="schnittgeschwindigkeit" />
        <Cell label="Spanvolumen Q" wert={erg.spanvolumen_q.toFixed(2)} einheit="cm³/min" hilfe="spanlast" />
      </div>
      {erg.warnungen.length > 0 && (
        <ul className="mt-2 space-y-1 text-xs">
          {erg.warnungen.map((w, i) => (
            <li
              key={i}
              className={clsx(
                w.stufe === "kritisch" && "text-camwosa-danger",
                w.stufe === "warnung" && "text-camwosa-warn",
                w.stufe === "info" && "text-camwosa-muted",
              )}
            >
              [{w.stufe}] {w.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Cell({
  label, wert, einheit, hilfe,
}: {
  label: string;
  wert: string;
  einheit: string;
  hilfe?: keyof typeof FACHBEGRIFFE;
}) {
  return (
    <div>
      <div className="flex items-center text-camwosa-muted">
        {label}
        {hilfe && <FachTooltip {...FACHBEGRIFFE[hilfe]} />}
      </div>
      <div className="font-mono">
        {wert} <span className="text-[10px] text-camwosa-muted">{einheit}</span>
      </div>
    </div>
  );
}
