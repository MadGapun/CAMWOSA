import { useTranslation } from "react-i18next";

export default function WorkflowView() {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.workflow")}</h1>
      <div className="rounded border border-gray-700 bg-camwosa-surface p-6 text-sm text-camwosa-muted">
        Multi-Setup-Editor mit Setup-Pausen, Foto-Slot und Arbeitsplan-PDF —
        Backend ist bereit, UI folgt. Backend-Funktion:
        <code className="ml-1 text-camwosa-accent">camwosa.workflow</code>
      </div>
    </div>
  );
}
