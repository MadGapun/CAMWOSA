/**
 * Sicherheits-Override-Dialog.
 *
 * Bei kritischen Sicherheits-Bloeckern (z.B. G0-im-Material) verhindert die
 * UI den Export. Wenn der User trotzdem exportieren will, muss er hier
 * explizit "VERSTANDEN" eingeben. Das verhindert versehentliches Wegklicken.
 */

import { useState } from "react";
import Modal from "./Modal";
import type { CheckBericht } from "../api/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onOverride: (begruendung: string) => void;
  bericht: CheckBericht;
}

const PFLICHT_TEXT = "VERSTANDEN";

export default function SicherheitsOverrideDialog({
  open, onClose, onOverride, bericht,
}: Props) {
  const [eingabe, setEingabe] = useState("");
  const [begruendung, setBegruendung] = useState("");

  function bestaetigen() {
    if (eingabe.trim() !== PFLICHT_TEXT) return;
    onOverride(begruendung);
    setEingabe("");
    setBegruendung("");
  }

  const kritisch = bericht.ergebnisse.filter((e) => e.stufe === "kritisch");

  return (
    <Modal open={open} onClose={onClose} titel="⚠ Sicherheits-Override" breit>
      <div className="space-y-4">
        <div className="rounded border border-camwosa-danger bg-red-950/40 p-3 text-sm">
          <strong className="text-camwosa-danger">
            {kritisch.length} kritische Sicherheits-Probleme erkannt!
          </strong>
          <ul className="mt-2 space-y-1 text-xs">
            {kritisch.map((e, i) => (
              <li key={i}>
                <strong>{e.titel}:</strong> {e.beschreibung}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-sm">
          Wenn du trotzdem exportieren willst, tippe bitte
          <code className="mx-1 rounded bg-camwosa-bg px-1 text-camwosa-accent">
            {PFLICHT_TEXT}
          </code>
          in das Feld unten und gib eine kurze Begruendung an. Der Override
          wird im Projekt-Audit-Log mit Timestamp protokolliert.
        </p>

        <div>
          <label className="mb-1 block text-xs text-camwosa-muted">
            Tippe genau „{PFLICHT_TEXT}"
          </label>
          <input
            type="text"
            className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm"
            value={eingabe}
            onChange={(e) => setEingabe(e.target.value)}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs text-camwosa-muted">
            Begruendung (kommt ins Audit-Log)
          </label>
          <textarea
            className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm"
            rows={2}
            value={begruendung}
            onChange={(e) => setBegruendung(e.target.value)}
            placeholder="z.B. „Test in Schaumstoff — Risiko bekannt"
          />
        </div>

        <div className="flex justify-end gap-2">
          <button
            className="rounded border border-gray-600 px-4 py-2 text-sm"
            onClick={onClose}
          >
            Abbrechen
          </button>
          <button
            className="rounded bg-camwosa-danger px-4 py-2 text-sm font-semibold text-white disabled:opacity-30"
            onClick={bestaetigen}
            disabled={eingabe.trim() !== PFLICHT_TEXT}
          >
            Trotzdem exportieren
          </button>
        </div>
      </div>
    </Modal>
  );
}
