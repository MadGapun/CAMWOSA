import { useTranslation } from "react-i18next";
import { useAktiveMaschine } from "../state/store";

export default function Topbar() {
  const { t } = useTranslation();
  const aktiveMaschine = useAktiveMaschine();
  return (
    <header className="flex h-12 items-center justify-between border-b border-gray-700 bg-camwosa-surface px-4">
      <div className="flex items-center gap-3">
        <span className="text-lg font-bold text-camwosa-accent">{t("app.name")}</span>
        <span className="text-sm text-camwosa-muted">{t("app.untertitel")}</span>
      </div>
      <div className="text-sm text-camwosa-muted">
        {aktiveMaschine ? `${t("maschine.titel")}: ${aktiveMaschine.name}` : ""}
      </div>
    </header>
  );
}
