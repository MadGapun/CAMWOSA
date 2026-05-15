import { useTranslation } from "react-i18next";

export default function EinstellungenView() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.einstellungen")}</h1>
      <div className="rounded border border-gray-700 bg-camwosa-surface p-6 text-sm">
        <p className="text-camwosa-muted">
          Theme, Sprache (DE/EN), Pfade, Update-Verhalten, KI-Features —
          wird in naechster Iteration befuellt.
        </p>
      </div>
    </div>
  );
}
