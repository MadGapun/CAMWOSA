import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAktiveVariante, useVarianteStore } from "../state/varianteStore";
import Modal from "./Modal";

/**
 * Kompakter Switcher fuer die aktive Variante (Topbar).
 *
 * - Dropdown listet alle Varianten + zeigt die aktive
 * - Klick auf das Zahnrad oeffnet das Verwaltungs-Modal
 * - Wenn nur eine Variante existiert, wird der Switcher trotzdem angezeigt
 *   damit der User schnell eine neue anlegen kann.
 */
export default function VarianteSwitcher() {
  const { t } = useTranslation();
  const varianten = useVarianteStore((s) => s.varianten);
  const aktiveVarianteId = useVarianteStore((s) => s.aktiveVarianteId);
  const wechseln = useVarianteStore((s) => s.wechseln);
  const aktive = useAktiveVariante();
  const [verwaltenOffen, setVerwaltenOffen] = useState(false);

  return (
    <>
      <label
        className="hidden items-center gap-1 md:flex"
        title={t("variante.aktive_tooltip", "Aktive Variante umschalten")}
      >
        <span className="text-camwosa-muted">V:</span>
        <select
          value={aktiveVarianteId ?? ""}
          onChange={(e) => wechseln(e.target.value)}
          className="max-w-[10rem] truncate rounded border border-camwosa-default bg-camwosa-bg px-1 py-0.5 text-xs lg:max-w-none"
        >
          {varianten.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="rounded border border-camwosa-default px-1.5 py-0.5 text-xs text-camwosa-muted hover:bg-camwosa-bg hover:text-camwosa-text"
          onClick={() => setVerwaltenOffen(true)}
          title={t("variante.verwalten", "Varianten verwalten")}
          aria-label={t("variante.verwalten", "Varianten verwalten")}
        >
          ⚙
        </button>
        {aktive && aktive.operationen.length > 0 && (
          <span className="hidden text-[10px] text-camwosa-muted xl:inline">
            {aktive.operationen.length} Op · {aktive.setups.length} Setup
          </span>
        )}
      </label>

      <VarianteVerwaltenModal
        open={verwaltenOffen}
        onClose={() => setVerwaltenOffen(false)}
      />
    </>
  );
}

interface ModalProps {
  open: boolean;
  onClose: () => void;
}

/**
 * Verwaltungs-Modal: anlegen, duplizieren, umbenennen, Notizen, loeschen.
 */
function VarianteVerwaltenModal({ open, onClose }: ModalProps) {
  const { t } = useTranslation();
  const varianten = useVarianteStore((s) => s.varianten);
  const aktiveVarianteId = useVarianteStore((s) => s.aktiveVarianteId);
  const erstellen = useVarianteStore((s) => s.erstellen);
  const umbenennen = useVarianteStore((s) => s.umbenennen);
  const notizenSetzen = useVarianteStore((s) => s.notizenSetzen);
  const loeschen = useVarianteStore((s) => s.loeschen);
  const wechseln = useVarianteStore((s) => s.wechseln);

  const [neuerName, setNeuerName] = useState("");

  function handleErstellen(duplizieren: boolean) {
    const name = neuerName.trim() || t("variante.unbenannt", "Neue Variante");
    erstellen(name, duplizieren ? aktiveVarianteId ?? undefined : undefined);
    setNeuerName("");
  }

  return (
    <Modal
      open={open}
      titel={t("variante.titel", "Varianten")}
      onClose={onClose}
      breit
    >
      <div className="space-y-4 text-sm">
        <p className="text-camwosa-muted">
          {t(
            "variante.beschreibung",
            "Varianten teilen die Geometrie, koennen aber unterschiedliche Operationen, Setups und Rohmaterial nutzen.",
          )}
        </p>

        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-camwosa-default text-left text-xs uppercase text-camwosa-muted">
              <th className="py-2 pr-2">{t("variante.spalte_aktiv", "Aktiv")}</th>
              <th className="py-2 pr-2">{t("variante.spalte_name", "Name")}</th>
              <th className="py-2 pr-2">{t("variante.spalte_inhalt", "Inhalt")}</th>
              <th className="py-2 pr-2">{t("variante.spalte_notizen", "Notizen")}</th>
              <th className="py-2 pr-2">{t("variante.spalte_aktionen", "")}</th>
            </tr>
          </thead>
          <tbody>
            {varianten.map((v) => (
              <tr key={v.id} className="border-b border-camwosa-default/60 align-top">
                <td className="py-2 pr-2">
                  <input
                    type="radio"
                    name="aktive_variante"
                    checked={v.id === aktiveVarianteId}
                    onChange={() => wechseln(v.id)}
                    title={t("variante.aktiv_setzen", "Diese Variante aktiv setzen")}
                  />
                </td>
                <td className="py-2 pr-2">
                  <input
                    type="text"
                    value={v.name}
                    onChange={(e) => umbenennen(v.id, e.target.value)}
                    className="w-full rounded border border-camwosa-default bg-camwosa-bg px-2 py-1"
                  />
                </td>
                <td className="py-2 pr-2 text-xs text-camwosa-muted">
                  {v.operationen.length}&nbsp;Op&nbsp;·&nbsp;{v.setups.length}&nbsp;Setup
                </td>
                <td className="py-2 pr-2">
                  <textarea
                    value={v.notizen}
                    onChange={(e) => notizenSetzen(v.id, e.target.value)}
                    rows={2}
                    className="w-full rounded border border-camwosa-default bg-camwosa-bg px-2 py-1 text-xs"
                  />
                </td>
                <td className="py-2 pr-2">
                  <button
                    type="button"
                    className="rounded border border-red-700 px-2 py-1 text-xs text-red-300 hover:bg-red-900/40 disabled:opacity-40"
                    onClick={() => loeschen(v.id)}
                    disabled={varianten.length <= 1}
                    title={
                      varianten.length <= 1
                        ? t(
                            "variante.loeschen_disabled",
                            "Die letzte Variante kann nicht geloescht werden.",
                          )
                        : t("variante.loeschen", "Loeschen")
                    }
                  >
                    {t("buttons.loeschen", "Loeschen")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex flex-wrap items-center gap-2 border-t border-camwosa-default pt-3">
          <input
            type="text"
            value={neuerName}
            onChange={(e) => setNeuerName(e.target.value)}
            placeholder={t("variante.neuer_name_placeholder", "Name der neuen Variante")}
            className="min-w-[14rem] flex-1 rounded border border-camwosa-default bg-camwosa-bg px-2 py-1"
          />
          <button
            type="button"
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-medium text-white hover:opacity-90"
            onClick={() => handleErstellen(false)}
          >
            + {t("variante.neu", "Leere Variante")}
          </button>
          <button
            type="button"
            className="rounded border border-camwosa-accent px-3 py-1 text-xs font-medium text-camwosa-accent hover:bg-camwosa-accent-soft"
            onClick={() => handleErstellen(true)}
          >
            ⧉ {t("variante.duplizieren", "Aktive duplizieren")}
          </button>
        </div>
      </div>
    </Modal>
  );
}
