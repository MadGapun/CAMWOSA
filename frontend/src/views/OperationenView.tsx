import { useTranslation } from "react-i18next";

export default function OperationenView() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.operationen")}</h1>
      <div className="rounded border border-gray-700 bg-camwosa-surface p-6 text-sm text-camwosa-muted">
        Operations-Editor (Kontur / Tasche / Bohren / Gravur / Relief) — UI wird in
        naechster Iteration befuellt. Backend-API ist bereits funktional, siehe
        <code className="ml-1 text-camwosa-accent">/api/operations/...</code>
      </div>
    </div>
  );
}
