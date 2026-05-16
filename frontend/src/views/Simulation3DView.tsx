import { useTranslation } from "react-i18next";
import Simulation3D from "../components/Simulation3D";
import { useAppStore } from "../state/store";
import { useRohmaterialStore } from "../state/rohmaterialStore";

export default function Simulation3DView() {
  const { t } = useTranslation();
  const operationen = useAppStore((s) => s.operationen);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const rohmaterial = useRohmaterialStore((s) => s.rohmaterial);

  const aktiveOps = operationen.filter((o) => o.aktiviert && o.toolpath);
  const toolpaths = aktiveOps.map((o) => o.toolpath!);
  const werkzeug = aktiveOps[0]
    ? werkzeuge.find((w) => w.id === aktiveOps[0].werkzeug_id)
    : null;

  return (
    <div className="space-y-2">
      <h1 className="text-xl font-bold">{t("navigation.preview")} (3D)</h1>
      {toolpaths.length === 0 ? (
        <div className="rounded border border-gray-700 bg-camwosa-surface p-6 text-sm text-camwosa-muted">
          Keine berechneten Toolpaths. Erst Operation berechnen in „Operationen".
        </div>
      ) : (
        <Simulation3D
          toolpaths={toolpaths}
          rohmaterial={{
            laenge: rohmaterial.laenge,
            breite: rohmaterial.breite,
            hoehe: rohmaterial.hoehe,
          }}
          werkzeugDurchmesser={werkzeug?.durchmesser ?? 6}
        />
      )}
    </div>
  );
}
