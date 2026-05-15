import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";

export default function MaterialienView() {
  const { t } = useTranslation();
  const materialien = useAppStore((s) => s.materialien);

  const grouped = materialien.reduce<Record<string, typeof materialien>>((acc, m) => {
    (acc[m.kategorie] ??= []).push(m);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.materialien")}</h1>
      {Object.entries(grouped).map(([kat, items]) => (
        <section key={kat}>
          <h2 className="mb-2 font-semibold capitalize">{kat}</h2>
          <ul className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {items.map((m) => (
              <li key={m.id} className="rounded border border-gray-700 bg-camwosa-surface p-3">
                <div className="font-medium">{m.name}</div>
                <div className="text-xs text-camwosa-muted">{m.unter_kategorie}</div>
                {m.janka_haerte != null && (
                  <div className="mt-1 text-xs">Janka: {m.janka_haerte}</div>
                )}
                <div className="mt-1 text-xs text-camwosa-muted">
                  {m.presets.length} Presets
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
