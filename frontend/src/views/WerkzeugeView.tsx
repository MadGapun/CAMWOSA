import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";

export default function WerkzeugeView() {
  const { t } = useTranslation();
  const werkzeuge = useAppStore((s) => s.werkzeuge);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.werkzeuge")}</h1>
      <table className="w-full text-sm">
        <thead className="border-b border-gray-700 text-left text-xs uppercase text-camwosa-muted">
          <tr>
            <th className="py-2">{t("werkzeug.titel")}</th>
            <th>{t("werkzeug.typ")}</th>
            <th>{t("werkzeug.durchmesser")}</th>
            <th>{t("werkzeug.schneiden")}</th>
            <th>{t("werkzeug.schneidlaenge")}</th>
          </tr>
        </thead>
        <tbody>
          {werkzeuge.map((w) => (
            <tr key={w.id} className="border-b border-gray-800 hover:bg-camwosa-surface">
              <td className="py-2">{w.name}</td>
              <td>{w.typ}</td>
              <td>{w.durchmesser} mm</td>
              <td>{w.schneiden}</td>
              <td>{w.schneidlaenge} mm</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
