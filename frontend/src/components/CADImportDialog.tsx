import { useEffect, useState } from "react";
import Modal from "./Modal";
import { camwosaApi } from "../api/client";
import type { DXFImportErgebnis } from "../api/types";
import { useAppStore } from "../state/store";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface FormatInfo {
  id: string;
  name: string;
  extensions: string[];
  beschreibung: string;
}

export default function CADImportDialog({ open, onClose }: Props) {
  const [datei, setDatei] = useState<File | null>(null);
  const [ergebnis, setErgebnis] = useState<
    (DXFImportErgebnis & { format_id?: string; metadaten?: Record<string, unknown> }) | null
  >(null);
  const [formate, setFormate] = useState<FormatInfo[]>([]);
  const [layerAuswahl, setLayerAuswahl] = useState<Record<string, boolean>>({});
  const [ladend, setLadend] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  const setGeometrien = useAppStore((s) => s.setGeometrien);

  useEffect(() => {
    if (!open) return;
    void camwosaApi.cadFormate().then(setFormate).catch(() => setFormate([]));
  }, [open]);

  async function analysieren() {
    if (!datei) return;
    setLadend(true);
    setFehler(null);
    try {
      const e = await camwosaApi.cadImport(datei);
      setErgebnis(e);
      const init: Record<string, boolean> = {};
      e.layer.forEach((l) => (init[l] = true));
      setLayerAuswahl(init);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFehler(`Fehler beim Importieren: ${msg}`);
    } finally {
      setLadend(false);
    }
  }

  function uebernehmen() {
    if (!ergebnis) return;
    const geos = ergebnis.objekte.filter((o) => layerAuswahl[o.layer] !== false);
    setGeometrien(geos);
    onClose();
    setErgebnis(null);
    setDatei(null);
  }

  const acceptList = formate.flatMap((f) => f.extensions).join(",");

  return (
    <Modal open={open} onClose={onClose} titel="CAD importieren">
      <div className="space-y-3">
        {formate.length > 0 && (
          <div className="rounded bg-camwosa-bg p-2 text-xs text-camwosa-muted">
            <strong>Unterstuetzte Formate:</strong>{" "}
            {formate.map((f) => f.extensions.join("/")).join(" · ")}
          </div>
        )}

        <input
          type="file"
          accept={acceptList || ".dxf,.svg,.stl,.step,.stp,.iges,.igs"}
          onChange={(e) => setDatei(e.target.files?.[0] ?? null)}
          className="w-full text-sm"
        />

        {datei && !ergebnis && (
          <button
            className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            onClick={() => void analysieren()}
            disabled={ladend}
          >
            {ladend ? "Analysiere..." : "Analysieren"}
          </button>
        )}

        {fehler && (
          <div className="rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
            {fehler}
          </div>
        )}

        {ergebnis && (
          <div className="space-y-3">
            <div className="rounded bg-camwosa-bg p-3 text-sm">
              <p>
                <strong>Format:</strong> {ergebnis.format_id ?? "?"}
              </p>
              <p>
                <strong>Einheit:</strong> {ergebnis.einheit}
              </p>
              <p>
                <strong>Objekte:</strong> {ergebnis.anzahl_objekte}
              </p>
              {ergebnis.bounding_box && (
                <p>
                  <strong>Bounding-Box:</strong>{" "}
                  {ergebnis.bounding_box.min[0].toFixed(1)},
                  {ergebnis.bounding_box.min[1].toFixed(1)} →{" "}
                  {ergebnis.bounding_box.max[0].toFixed(1)},
                  {ergebnis.bounding_box.max[1].toFixed(1)} mm
                </p>
              )}
              {ergebnis.metadaten && Object.keys(ergebnis.metadaten).length > 0 && (
                <pre className="mt-2 max-h-32 overflow-auto text-xs text-camwosa-muted">
                  {JSON.stringify(ergebnis.metadaten, null, 2)}
                </pre>
              )}
            </div>

            {ergebnis.layer.length > 0 && (
              <div>
                <h3 className="mb-2 text-sm font-semibold">Layer-Auswahl</h3>
                <ul className="space-y-1 text-sm">
                  {ergebnis.layer.map((l) => {
                    const anzahl = ergebnis.objekte.filter((o) => o.layer === l).length;
                    return (
                      <li key={l} className="flex items-center justify-between">
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={layerAuswahl[l] !== false}
                            onChange={(e) =>
                              setLayerAuswahl((s) => ({ ...s, [l]: e.target.checked }))
                            }
                          />
                          {l}
                        </label>
                        <span className="text-xs text-camwosa-muted">
                          {anzahl} Objekte
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {ergebnis.einheit === "inch" && (
              <div className="rounded border border-camwosa-warn bg-yellow-950/30 p-2 text-xs text-camwosa-warn">
                ⚠ Datei in Zoll. Bitte vor Verwendung skalieren — CAMWOSA arbeitet in mm.
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                className="rounded border border-gray-600 px-4 py-2 text-sm"
                onClick={onClose}
              >
                Abbrechen
              </button>
              <button
                className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white"
                onClick={uebernehmen}
                disabled={ergebnis.anzahl_objekte === 0}
              >
                Uebernehmen
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
