import { useTranslation } from "react-i18next";
import { useAktiveMaschine, useAktiveSpindel } from "../state/store";

export default function Topbar() {
  const { t } = useTranslation();
  const aktiveMaschine = useAktiveMaschine();
  const aktiveSpindel = useAktiveSpindel();
  return (
    <header className="flex h-12 items-center justify-between border-b border-gray-700 bg-camwosa-surface px-4">
      <div className="flex items-center gap-3">
        <span className="text-lg font-bold text-camwosa-accent">{t("app.name")}</span>
        <span className="text-sm text-camwosa-muted">{t("app.untertitel")}</span>
      </div>
      <div className="flex items-center gap-4 text-sm text-camwosa-muted">
        {aktiveMaschine && (
          <span>
            <span className="text-camwosa-muted">{t("maschine.titel")}:</span>{" "}
            <span className="text-camwosa-text">{aktiveMaschine.name}</span>
          </span>
        )}
        {aktiveSpindel && (
          <span>
            <span className="text-camwosa-muted">Spindel:</span>{" "}
            <span className="text-camwosa-text">{aktiveSpindel.name}</span>
            <span className="ml-1 text-xs">
              ({aktiveSpindel.rpm_min}–{aktiveSpindel.rpm_max} RPM)
            </span>
          </span>
        )}
      </div>
    </header>
  );
}
