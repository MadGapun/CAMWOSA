import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";

export default function StatusBar() {
  const { t } = useTranslation();
  const backendOk = useAppStore((s) => s.backendOk);
  const setBackendOk = useAppStore((s) => s.setBackendOk);
  const setStammdaten = useAppStore((s) => s.setStammdaten);

  useEffect(() => {
    let cancel = false;
    async function init() {
      try {
        await camwosaApi.health();
        if (cancel) return;
        setBackendOk(true);
        const [m, w, mat] = await Promise.all([
          camwosaApi.maschinen(),
          camwosaApi.werkzeuge(),
          camwosaApi.materialien(),
        ]);
        if (cancel) return;
        setStammdaten(m, w, mat);
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
      <div className="text-camwosa-muted">CAMWOSA v0.1.0</div>
    </footer>
  );
}
