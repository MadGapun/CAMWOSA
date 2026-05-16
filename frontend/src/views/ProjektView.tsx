import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";
import CADImportDialog from "../components/CADImportDialog";
import RohmaterialEditor from "../components/RohmaterialEditor";

export default function ProjektView() {
  const { t } = useTranslation();
  const maschinen = useAppStore((s) => s.maschinen);
  const materialien = useAppStore((s) => s.materialien);
  const aktiveMaschineId = useAppStore((s) => s.aktiveMaschineId);
  const setAktiveMaschine = useAppStore((s) => s.setAktiveMaschine);
  const aktivesMaterialId = useAppStore((s) => s.aktivesMaterialId);
  const setAktivesMaterial = useAppStore((s) => s.setAktivesMaterial);
  const geometrien = useAppStore((s) => s.geometrien);
  const operationen = useAppStore((s) => s.operationen);
  const geometrienLeeren = useAppStore((s) => s.geometrienLeeren);
  const spindeln = useAppStore((s) => s.spindeln);
  const aktiveSpindelId = useAppStore((s) => s.aktiveSpindelId);
  const setAktiveSpindelId = useAppStore((s) => s.setAktiveSpindelId);

  const aktiveMaschine = maschinen.find((m) => m.id === aktiveMaschineId);
  const verfuegbareSpindeln = aktiveMaschine
    ? spindeln.filter((sp) => aktiveMaschine.spindel_ids.includes(sp.id))
    : [];
  const effektiveSpindelId =
    aktiveSpindelId ?? aktiveMaschine?.aktive_spindel_id ?? null;

  const [dxfOffen, setDxfOffen] = useState(false);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("projekt.titel")}</h1>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">{t("maschine.auswahl")}</h2>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="mb-1 block text-xs text-camwosa-muted">
              {t("maschine.titel")}
            </label>
            <select
              className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm"
              value={aktiveMaschineId ?? ""}
              onChange={(e) => {
                setAktiveMaschine(e.target.value || null);
                setAktiveSpindelId(null);  // Override loeschen, Maschinen-Default greift
              }}
            >
              <option value="">— bitte waehlen —</option>
              {maschinen.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-camwosa-muted">
              Spindel
              {aktiveSpindelId === null && aktiveMaschine?.aktive_spindel_id && (
                <span className="ml-1 text-[10px]">(Default aus Maschine)</span>
              )}
            </label>
            <select
              className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm disabled:opacity-50"
              value={effektiveSpindelId ?? ""}
              disabled={!aktiveMaschine || verfuegbareSpindeln.length === 0}
              onChange={(e) => setAktiveSpindelId(e.target.value || null)}
            >
              {verfuegbareSpindeln.length === 0 && (
                <option value="">— keine Spindeln zugeordnet —</option>
              )}
              {verfuegbareSpindeln.map((sp) => (
                <option key={sp.id} value={sp.id}>
                  {sp.name} ({sp.rpm_min}–{sp.rpm_max} RPM)
                </option>
              ))}
            </select>
            {aktiveSpindelId !== null && (
              <button
                className="mt-1 text-[10px] text-camwosa-muted hover:text-camwosa-accent"
                onClick={() => setAktiveSpindelId(null)}
              >
                ↺ auf Maschinen-Default zuruecksetzen
              </button>
            )}
          </div>
          <div>
            <label className="mb-1 block text-xs text-camwosa-muted">Material</label>
            <select
              className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm"
              value={aktivesMaterialId ?? ""}
              onChange={(e) => setAktivesMaterial(e.target.value || null)}
            >
              <option value="">— bitte waehlen —</option>
              {materialien.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Rohmaterial</h2>
        <RohmaterialEditor />
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Geometrie</h2>
        <div className="flex items-center gap-3">
          <button
            className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white"
            onClick={() => setDxfOffen(true)}
          >
            CAD importieren
          </button>
          {geometrien.length > 0 && (
            <>
              <span className="text-sm text-camwosa-muted">
                {geometrien.length} Objekte geladen (
                {geometrien.filter((g) => g.geschlossen).length} geschlossen)
              </span>
              <button
                className="text-xs text-camwosa-muted hover:text-camwosa-danger"
                onClick={geometrienLeeren}
              >
                Loeschen
              </button>
            </>
          )}
        </div>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Operationen</h2>
        {operationen.length === 0 ? (
          <p className="text-sm text-camwosa-muted">
            Noch keine Operationen. Wechsle zu „Operationen" um eine anzulegen.
          </p>
        ) : (
          <ul className="space-y-1 text-sm">
            {operationen.map((op) => (
              <li key={op.id} className="flex items-center justify-between">
                <span>
                  <span className="text-camwosa-muted">{op.typ}:</span> {op.name}
                </span>
                <span className="text-xs text-camwosa-muted">
                  {op.toolpath ? `${op.toolpath.bewegungen.length} Bew.` : "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Schnellaktionen</h2>
        <div className="flex gap-2">
          <button className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white">
            {t("projekt.neu")}
          </button>
          <button className="rounded border border-gray-600 px-4 py-2 text-sm">
            {t("projekt.oeffnen")}
          </button>
        </div>
      </section>

      <CADImportDialog open={dxfOffen} onClose={() => setDxfOffen(false)} />
    </div>
  );
}
