import { useState } from "react";
import { useUIPrefs, type Density, type Theme, type VorschauModus } from "../state/uiPrefs";

/**
 * Kleines Pop-Menu in der Topbar — Theme, Dichte, Vorschau-Default.
 * Persistiert per LocalStorage (siehe state/uiPrefs.ts).
 */
export default function UIPrefsMenu() {
  const [offen, setOffen] = useState(false);
  const { theme, density, vorschauModusDefault, setTheme, setDensity, setVorschauModusDefault } =
    useUIPrefs();

  return (
    <div className="relative">
      <button
        className="rounded border border-camwosa-default px-2 py-1 text-xs hover:bg-camwosa-overlay"
        onClick={() => setOffen(!offen)}
        title="Anzeige-Einstellungen"
      >
        🎚
      </button>
      {offen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOffen(false)}
          />
          <div className="absolute right-0 top-9 z-50 w-64 rounded-lg border border-camwosa-default bg-camwosa-elevated p-3 shadow-lg">
            <Section label="Theme">
              <Radio<Theme>
                value={theme}
                onChange={setTheme}
                options={[
                  { v: "dark", l: "Dark" },
                  { v: "light", l: "Light" },
                ]}
              />
            </Section>
            <Section label="Dichte">
              <Radio<Density>
                value={density}
                onChange={setDensity}
                options={[
                  { v: "compact", l: "Kompakt", hint: "10\" Tablet" },
                  { v: "medium", l: "Mittel" },
                  { v: "comfortable", l: "Großzügig", hint: "Touch / 34\"" },
                ]}
              />
            </Section>
            <Section label="Live-Vorschau (Standard)">
              <Radio<VorschauModus>
                value={vorschauModusDefault}
                onChange={setVorschauModusDefault}
                options={[
                  { v: "aus", l: "Aus", hint: "Kein 3D-Overlay" },
                  { v: "vereinfacht", l: "Vereinfacht", hint: "Schnell" },
                  { v: "komplett", l: "Komplett", hint: "Voll, bei Relief teuer" },
                ]}
              />
              <p className="mt-1 text-[10px] text-camwosa-muted">
                Pro Operation ueberschreibbar im Vorschau-Header.
              </p>
            </Section>
          </div>
        </>
      )}
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-3 last:mb-0">
      <div className="mb-1 text-[10px] uppercase tracking-wider text-camwosa-muted">
        {label}
      </div>
      {children}
    </div>
  );
}

function Radio<T extends string>({
  value, onChange, options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: Array<{ v: T; l: string; hint?: string }>;
}) {
  return (
    <div className="grid grid-cols-1 gap-1">
      {options.map((o) => (
        <button
          key={o.v}
          onClick={() => onChange(o.v)}
          className={[
            "flex items-center justify-between rounded px-2 py-1 text-left text-xs transition",
            value === o.v
              ? "bg-camwosa-accent text-camwosa-bg"
              : "hover:bg-camwosa-overlay",
          ].join(" ")}
        >
          <span>{o.l}</span>
          {o.hint && (
            <span className={value === o.v ? "text-[10px] opacity-80" : "text-[10px] text-camwosa-muted"}>
              {o.hint}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
