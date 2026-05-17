import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiBereit, camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";

export default function StatusBar() {
  const { t } = useTranslation();
  const backendOk = useAppStore((s) => s.backendOk);
  const setBackendOk = useAppStore((s) => s.setBackendOk);
  const setStammdaten = useAppStore((s) => s.setStammdaten);
  const [version, setVersion] = useState<string>("…");

  useEffect(() => {
    let cancel = false;
    async function init() {
      try {
        // In Electron-Prod: warte auf die backendUrl-IPC-Aufloesung,
        // sonst koennen die ersten Calls noch ins Leere gehen.
        await apiBereit;
        const health = await camwosaApi.health();
        if (cancel) return;
        setBackendOk(true);
        if (health?.version) setVersion(health.version);
        const [m, w, mat, sp] = await Promise.all([
          camwosaApi.maschinen(),
          camwosaApi.werkzeuge(),
          camwosaApi.materialien(),
          camwosaApi.spindeln(),
        ]);
        if (cancel) return;
        setStammdaten(m, w, mat, sp);
      } catch {
        if (!cancel) setBackendOk(false);
      }
    }
    void init();
    const t = setInterval(init, 5000);
    return () => {
      cancel = true;
      clearInterval(t);
    };
  }, [setBackendOk, setStammdaten]);

  return (
    <footer className="flex h-7 items-center justify-between border-t border-gray-700 bg-camwosa-surface px-3 text-xs">
      <div className="flex items-center gap-2">
        <span
          className={
            backendOk
              ? "h-2 w-2 rounded-full bg-camwosa-ok"
              : "h-2 w-2 rounded-full bg-camwosa-danger"
          }
        />
        <span>{backendOk ? t("status.verbunden") : t("status.getrennt")}</span>
      </div>
      <div className="text-camwosa-muted">CAMWOSA v{version}</div>
    </footer>
  );
}
