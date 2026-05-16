import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import ToolpathStage from "../components/ToolpathStage";
import { useAppStore } from "../state/store";
import type { CheckErgebnis } from "../api/types";

/**
 * 2D-Toolpath-Vorschau (Konva).
 *
 * Zeigt alle Toolpaths der aktivierten Operationen + DXF-Geometrie als Hintergrund.
 * Sicherheits-Panel rechts mit Klick-zur-Stelle (markiert Bewegung in der Vorschau).
 */
export default function PreviewView() {
  const { t } = useTranslation();
  const operationen = useAppStore((s) => s.operationen);
  const geometrien = useAppStore((s) => s.geometrien);

  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [highlight, setHighlight] = useState<{
    toolpathIndex: number;
    bewegungIndex: number;
  } | null>(null);

  useEffect(() => {
    function fit() {
      if (!containerRef.current) return;
      const r = containerRef.current.getBoundingClientRect();
      setSize({ w: Math.floor(r.width), h: Math.max(400, window.innerHeight - 200) });
    }
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  const aktiveOps = operationen.filter((o) => o.aktiviert && o.toolpath);
  const toolpaths = aktiveOps.map((o) => o.toolpath!);
  const alleProbleme: Array<{
    opIndex: number;
    opName: string;
    ergebnis: CheckErgebnis;
  }> = [];
  aktiveOps.forEach((op, i) => {
    op.sicherheits_bericht?.ergebnisse.forEach((e) =>
      alleProbleme.push({ opIndex: i, opName: op.name, ergebnis: e }),
    );
  });

  return (
    <div className="space-y-2">
      <h1 className="text-xl font-bold">{t("navigation.preview")}</h1>

      <div className="grid grid-cols-12 gap-3">
        <div
          className="col-span-9 overflow-hidden rounded border border-gray-700 bg-camwosa-surface"
          ref={containerRef}
        >
          {toolpaths.length === 0 && geometrien.length === 0 ? (
            <div className="flex h-96 items-center justify-center text-sm text-camwosa-muted">
              Keine Daten — DXF importieren oder Operation berechnen.
            </div>
          ) : (
            <ToolpathStage
              width={size.w}
              height={size.h}
              toolpaths={toolpaths}
              geometrien={geometrien}
              highlightedBewegung={highlight}
            />
          )}
        </div>

        <aside className="col-span-3 space-y-3">
          <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
            <h2 className="mb-2 text-sm font-semibold">Operationen ({aktiveOps.length})</h2>
            {aktiveOps.length === 0 && (
              <p className="text-xs text-camwosa-muted">Keine berechneten Toolpaths.</p>
            )}
            <ul className="space-y-1 text-xs">
              {aktiveOps.map((op) => (
                <li key={op.id} className="flex items-center justify-between">
                  <span className="font-medium">{op.name}</span>
                  <span className="text-camwosa-muted">
                    {op.toolpath!.bewegungen.length} Bew.
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
            <h2 className="mb-2 text-sm font-semibold">{t("sicherheit.titel")}</h2>
            {alleProbleme.length === 0 ? (
              <p className="text-xs text-camwosa-ok">✓ Alles in Ordnung</p>
            ) : (
              <ul className="space-y-1 text-xs">
                {alleProbleme.map((p, i) => (
                  <li
                    key={i}
                    className={clsx(
                      "cursor-pointer rounded p-1.5 transition",
                      p.ergebnis.stufe === "kritisch" &&
                        "border border-camwosa-danger bg-red-950/30",
                      p.ergebnis.stufe === "warnung" &&
                        "border border-camwosa-warn bg-yellow-950/20",
                      p.ergebnis.stufe === "info" &&
                        "border border-gray-600 bg-camwosa-bg",
                    )}
                    onClick={() => {
                      if (p.ergebnis.bewegungs_index != null) {
                        setHighlight({
                          toolpathIndex: p.opIndex,
                          bewegungIndex: p.ergebnis.bewegungs_index,
                        });
                      }
                    }}
                  >
                    <div className="font-semibold">{p.ergebnis.titel}</div>
                    <div className="text-camwosa-muted">{p.opName}</div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
