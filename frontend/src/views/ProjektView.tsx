import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";

export default function ProjektView() {
  const { t } = useTranslation();
  const maschinen = useAppStore((s) => s.maschinen);
  const aktiveMaschineId = useAppStore((s) => s.aktiveMaschineId);
  const setAktiveMaschine = useAppStore((s) => s.setAktiveMaschine);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("projekt.titel")}</h1>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">{t("maschine.auswahl")}</h2>
        <select
          className="rounded bg-camwosa-bg px-3 py-2 text-sm"
          value={aktiveMaschineId ?? ""}
          onChange={(e) => setAktiveMaschine(e.target.value || null)}
        >
          <option value="">— bitte waehlen —</option>
          {maschinen.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
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
    </div>
  );
}
