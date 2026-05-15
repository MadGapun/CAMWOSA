import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";

export default function MaschinenView() {
  const { t } = useTranslation();
  const maschinen = useAppStore((s) => s.maschinen);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.maschinen")}</h1>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {maschinen.map((m) => (
          <div key={m.id} className="rounded border border-gray-700 bg-camwosa-surface p-4">
            <h3 className="font-semibold">{m.name}</h3>
            <p className="mt-1 text-sm text-camwosa-muted">{m.hersteller} · {m.modell}</p>
            <dl className="mt-3 grid grid-cols-2 gap-x-2 gap-y-1 text-xs">
              <dt className="text-camwosa-muted">{t("maschine.controller")}</dt>
              <dd>{m.controller}</dd>
              <dt className="text-camwosa-muted">{t("maschine.arbeitsraum")}</dt>
              <dd>{m.arbeitsraum.x}×{m.arbeitsraum.y}×{m.arbeitsraum.z} mm</dd>
              <dt className="text-camwosa-muted">RPM</dt>
              <dd>{m.spindel_rpm_min} – {m.spindel_rpm_max}</dd>
              <dt className="text-camwosa-muted">{t("maschine.modus")}</dt>
              <dd>{m.modi.join(", ")}</dd>
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}
