import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import clsx from "clsx";

const ROUTES = [
  { to: "/projekt", key: "projekt" },
  { to: "/maschinen", key: "maschinen" },
  { to: "/werkzeuge", key: "werkzeuge" },
  { to: "/materialien", key: "materialien" },
  { to: "/operationen", key: "operationen" },
  { to: "/preview", key: "preview" },
  { to: "/editor", key: "editor" },
  { to: "/workflow", key: "workflow" },
  { to: "/nesting", key: "nesting" },
  { to: "/einstellungen", key: "einstellungen" },
];

export default function Sidebar() {
  const { t } = useTranslation();
  return (
    <nav className="w-56 shrink-0 border-r border-gray-700 bg-camwosa-surface p-2">
      <ul className="space-y-1">
        {ROUTES.map((r) => (
          <li key={r.to}>
            <NavLink
              to={r.to}
              className={({ isActive }) =>
                clsx(
                  "block rounded px-3 py-2 text-sm transition",
                  isActive
                    ? "bg-camwosa-accent text-white"
                    : "text-camwosa-text hover:bg-gray-700",
                )
              }
            >
              {t(`navigation.${r.key}`)}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
