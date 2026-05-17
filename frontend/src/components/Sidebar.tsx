import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import clsx from "clsx";

interface RouteDef {
  to: string;
  key: string;
  icon: string;
  gruppe: "schnell" | "projekt" | "stammdaten" | "ausgabe";
}

const ROUTES: RouteDef[] = [
  { to: "/quickstart", key: "quickstart", icon: "⚡", gruppe: "schnell" },
  { to: "/projekt", key: "projekt", icon: "▤", gruppe: "projekt" },
  { to: "/zeichnen", key: "zeichnen", icon: "✎", gruppe: "projekt" },
  { to: "/operationen", key: "operationen", icon: "⚙", gruppe: "projekt" },
  { to: "/drechseln", key: "drechseln", icon: "◯", gruppe: "projekt" },
  { to: "/wrap", key: "wrap", icon: "◌", gruppe: "projekt" },
  { to: "/bild-relief", key: "bild_relief", icon: "🖼", gruppe: "projekt" },
  { to: "/workflow", key: "workflow", icon: "⇨", gruppe: "projekt" },
  { to: "/preview", key: "preview", icon: "▦", gruppe: "ausgabe" },
  { to: "/simulation", key: "simulation", icon: "◐", gruppe: "ausgabe" },
  { to: "/abtrag", key: "abtrag", icon: "▥", gruppe: "ausgabe" },
  { to: "/editor", key: "editor", icon: "{}", gruppe: "ausgabe" },
  { to: "/maschinen", key: "maschinen", icon: "▥", gruppe: "stammdaten" },
  { to: "/werkzeuge", key: "werkzeuge", icon: "↧", gruppe: "stammdaten" },
  { to: "/materialien", key: "materialien", icon: "▣", gruppe: "stammdaten" },
  { to: "/nesting", key: "nesting", icon: "▩", gruppe: "stammdaten" },
  { to: "/einstellungen", key: "einstellungen", icon: "⚙", gruppe: "stammdaten" },
];

const GRUPPEN_LABEL: Record<RouteDef["gruppe"], string> = {
  schnell: "Schnell",
  projekt: "Projekt",
  ausgabe: "Ausgabe",
  stammdaten: "Stammdaten",
};

function useIstSchmal() {
  const [schmal, setSchmal] = useState(false);
  useEffect(() => {
    const update = () => setSchmal(window.innerWidth < 900);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  return schmal;
}

export default function Sidebar() {
  const { t } = useTranslation();
  const istSchmal = useIstSchmal();
  const [eingeklappt, setEingeklappt] = useState(false);

  // Auf schmalen Displays automatisch icon-only Modus
  const iconOnly = istSchmal || eingeklappt;

  const gruppiert = ROUTES.reduce<Record<string, RouteDef[]>>((acc, r) => {
    (acc[r.gruppe] ??= []).push(r);
    return acc;
  }, {});

  return (
    <nav
      className={clsx(
        "shrink-0 border-r border-gray-700 bg-camwosa-surface p-2 transition-[width] duration-150",
        iconOnly ? "w-14" : "w-52",
      )}
    >
      <div className="mb-2 flex items-center justify-end">
        <button
          className="rounded p-1 text-xs text-camwosa-muted hover:bg-gray-700"
          onClick={() => setEingeklappt(!eingeklappt)}
          title={iconOnly ? "Sidebar ausklappen" : "Sidebar einklappen"}
        >
          {iconOnly ? "»" : "«"}
        </button>
      </div>

      <div className="space-y-3">
        {(["schnell", "projekt", "ausgabe", "stammdaten"] as const).map((g) => {
          const items = gruppiert[g] || [];
          if (!items.length) return null;
          return (
            <div key={g}>
              {!iconOnly && (
                <div className="mb-1 px-2 text-[10px] uppercase tracking-wider text-camwosa-muted">
                  {GRUPPEN_LABEL[g]}
                </div>
              )}
              <ul className="space-y-1">
                {items.map((r) => (
                  <li key={r.to}>
                    <NavLink
                      to={r.to}
                      title={t(`navigation.${r.key}`, r.key)}
                      className={({ isActive }) =>
                        clsx(
                          "flex items-center gap-2 rounded px-2 py-2 text-sm transition",
                          isActive
                            ? "bg-camwosa-accent text-white"
                            : "text-camwosa-text hover:bg-gray-700",
                          iconOnly ? "justify-center" : "",
                        )
                      }
                    >
                      <span className="w-5 text-center text-base">{r.icon}</span>
                      {!iconOnly && (
                        <span className="truncate">
                          {t(`navigation.${r.key}`, r.key)}
                        </span>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </nav>
  );
}
