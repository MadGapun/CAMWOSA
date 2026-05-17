import { useTranslation } from "react-i18next";
import { useAppStore, useAktiveMaschine, useAktiveSpindel } from "../state/store";
import UIPrefsMenu from "./UIPrefsMenu";
import VarianteSwitcher from "./VarianteSwitcher";

/**
 * Topbar mit App-Name, Maschine + Spindel als **Selektoren** (Design-Note 4 — Auswahl
 * bleibt jederzeit sichtbar, nicht im Einstellungsdialog versteckt), UI-Prefs + Claude-Link.
 *
 * Verhalten auf schmalen Displays:
 * - Untertitel ab ``md``
 * - Selektoren als Kompakt-Selects ab ``sm`` (10\" Tablet zeigt sie immer noch)
 * - Spindel-Auswahl ab ``md`` — auf 10\" reicht der Maschinen-Select
 */
export default function Topbar() {
  const { t } = useTranslation();
  const maschinen = useAppStore((s) => s.maschinen);
  const spindeln = useAppStore((s) => s.spindeln);
  const aktiveMaschineId = useAppStore((s) => s.aktiveMaschineId);
  const aktiveSpindelId = useAppStore((s) => s.aktiveSpindelId);
  const setAktiveMaschine = useAppStore((s) => s.setAktiveMaschine);
  const setAktiveSpindel = useAppStore((s) => s.setAktiveSpindelId);
  const aktiveMaschine = useAktiveMaschine();
  const aktiveSpindel = useAktiveSpindel();

  // Spindeln die fuer die aktive Maschine verfuegbar sind
  const verfuegbareSpindeln = aktiveMaschine
    ? spindeln.filter((sp) => aktiveMaschine.spindel_ids?.includes(sp.id))
    : spindeln;

  return (
    <header className="flex h-12 items-center justify-between gap-2 border-b border-camwosa-default bg-camwosa-surface px-3">
      <div className="flex min-w-0 items-center gap-2">
        <span className="text-base font-bold text-camwosa-accent md:text-lg">
          {t("app.name")}
        </span>
        <span className="hidden text-xs text-camwosa-muted md:inline md:text-sm">
          {t("app.untertitel")}
        </span>
      </div>

      <div className="flex min-w-0 items-center gap-2 text-xs">
        {/* Maschinen-Selector */}
        <label className="hidden items-center gap-1 sm:flex" title="Aktive Maschine">
          <span className="text-camwosa-muted">M:</span>
          <select
            value={aktiveMaschineId ?? ""}
            onChange={(e) => setAktiveMaschine(e.target.value || null)}
            className="max-w-[10rem] truncate rounded border border-camwosa-default bg-camwosa-bg px-1 py-0.5 text-xs lg:max-w-none"
          >
            <option value="">— keine —</option>
            {maschinen.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </label>

        {/* Spindel-Selector — wichtig wenn Maschine mehrere Spindeln hat */}
        <label className="hidden items-center gap-1 md:flex" title="Aktive Spindel">
          <span className="text-camwosa-muted">S:</span>
          <select
            value={aktiveSpindelId ?? aktiveMaschine?.aktive_spindel_id ?? ""}
            onChange={(e) => setAktiveSpindel(e.target.value || null)}
            disabled={verfuegbareSpindeln.length === 0}
            className="max-w-[10rem] truncate rounded border border-camwosa-default bg-camwosa-bg px-1 py-0.5 text-xs lg:max-w-none"
          >
            <option value="">— Default —</option>
            {verfuegbareSpindeln.map((sp) => (
              <option key={sp.id} value={sp.id}>{sp.name}</option>
            ))}
          </select>
          {aktiveSpindel && (
            <span className="hidden text-[10px] text-camwosa-muted xl:inline">
              {aktiveSpindel.rpm_min}–{aktiveSpindel.rpm_max}
            </span>
          )}
        </label>

        <VarianteSwitcher />

        <UIPrefsMenu />

        <a
          href="https://claude.ai/new"
          target="_blank"
          rel="noreferrer noopener"
          title="Claude in eigenem Browser-Tab oeffnen"
          className="rounded border border-camwosa-accent/60 bg-camwosa-accent-soft px-2 py-1 text-xs font-medium text-camwosa-accent hover:opacity-90"
        >
          💬
        </a>
      </div>
    </header>
  );
}
