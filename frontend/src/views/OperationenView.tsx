import { useState } from "react";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import { camwosaApi } from "../api/client";
import type {
  BohrParameter,
  CheckBericht,
  GeometrieObjekt,
  GravurParameter,
  KonturParameter,
  OperationEintrag,
  OperationsTyp,
  TaschenParameter,
  Toolpath,
} from "../api/types";
import { useAktiveMaschine, useAppStore } from "../state/store";
import OverrideOperationForm from "../components/OverrideOperationForm";
import FeedsSpeedsPanel from "../components/FeedsSpeedsPanel";

const OP_LABELS: Record<OperationsTyp, string> = {
  kontur: "Kontur",
  tasche: "Tasche",
  bohren: "Bohren",
  gravur: "Gravur",
  relief: "Relief",
  eilgang: "Eilgang",
};

function uniqId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
}

export default function OperationenView() {
  const { t } = useTranslation();
  const maschine = useAktiveMaschine();
  const aktivesMaterialId = useAppStore((s) => s.aktivesMaterialId);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const geometrien = useAppStore((s) => s.geometrien);
  const operationen = useAppStore((s) => s.operationen);
  const aktiveOpId = useAppStore((s) => s.aktiveOperationId);
  const setAktiveOpId = useAppStore((s) => s.setAktiveOperationId);
  const opHinzufuegen = useAppStore((s) => s.operationHinzufuegen);
  const opAktualisieren = useAppStore((s) => s.operationAktualisieren);
  const opLoeschen = useAppStore((s) => s.operationLoeschen);

  const [berechneFehler, setBerechneFehler] = useState<string | null>(null);
  const [berechneLaeuft, setBerechneLaeuft] = useState(false);

  const aktiveOp = operationen.find((o) => o.id === aktiveOpId) ?? null;

  function neueOperation(typ: OperationsTyp) {
    if (werkzeuge.length === 0) return;
    const wid = werkzeuge[0].id;
    const op: OperationEintrag = {
      id: uniqId("op"),
      name: `${OP_LABELS[typ]} ${operationen.length + 1}`,
      typ,
      werkzeug_id: wid,
      geometrie_id: null,
      // Parameter = Overrides: nur werkzeug_id ist gesetzt, alles andere aus Material-Preset
      parameter: { werkzeug_id: wid } as unknown as KonturParameter,
      aktiviert: true,
    };
    opHinzufuegen(op);
    setAktiveOpId(op.id);
  }

  async function berechnen(op: OperationEintrag) {
    if (!maschine) {
      setBerechneFehler("Bitte zuerst eine Maschine im Projekt waehlen.");
      return;
    }
    if (!aktivesMaterialId) {
      setBerechneFehler("Bitte zuerst ein Material im Projekt waehlen.");
      return;
    }
    setBerechneLaeuft(true);
    setBerechneFehler(null);
    try {
      // 1) Overrides auflosen -> volle Parameter
      const overrides = {
        ...(op.parameter as unknown as Record<string, unknown>),
        werkzeug_id: op.werkzeug_id,
      };
      const aufgeloest = await camwosaApi.opAufloesen(
        op.typ as "kontur" | "tasche" | "bohren" | "gravur",
        aktivesMaterialId,
        overrides,
      );
      const param = aufgeloest.parameter;

      // 2) Toolpath berechnen
      let tp: Toolpath | null = null;
      if (op.typ === "kontur") {
        const geo = waehleGeometrie(op, geometrien);
        if (!geo) throw new Error("Keine Geometrie zugewiesen.");
        tp = await camwosaApi.opKontur(op.werkzeug_id, geo, param as unknown as KonturParameter);
      } else if (op.typ === "tasche") {
        const geo = waehleGeometrie(op, geometrien);
        if (!geo) throw new Error("Keine geschlossene Geometrie zugewiesen.");
        tp = await camwosaApi.opTasche(op.werkzeug_id, geo, param as unknown as TaschenParameter);
      } else if (op.typ === "bohren") {
        const punkte = bohrpunkte(geometrien);
        if (punkte.length === 0) throw new Error("Keine Bohrpunkte gefunden (KREIS/PUNKT).");
        tp = await camwosaApi.opBohren(op.werkzeug_id, punkte, param as unknown as BohrParameter);
      } else if (op.typ === "gravur") {
        const geo = waehleGeometrie(op, geometrien);
        if (!geo) throw new Error("Keine Geometrie zugewiesen.");
        tp = await camwosaApi.opGravur(op.werkzeug_id, geo, param as unknown as GravurParameter);
      }
      if (!tp) return;

      // 3) Sicherheits-Check
      const bericht: CheckBericht = await camwosaApi.safetyCheck(
        maschine.id,
        op.werkzeug_id,
        tp,
        0.0,
      );
      opAktualisieren(op.id, { toolpath: tp, sicherheits_bericht: bericht });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setBerechneFehler(msg);
    } finally {
      setBerechneLaeuft(false);
    }
  }

  function alleAufStandard(op: OperationEintrag) {
    // Alle Overrides leeren ausser werkzeug_id
    opAktualisieren(op.id, {
      parameter: { werkzeug_id: op.werkzeug_id } as unknown as KonturParameter,
    });
  }

  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Liste links */}
      <aside className="col-span-3 rounded border border-gray-700 bg-camwosa-surface">
        <header className="border-b border-gray-700 px-3 py-2">
          <h2 className="text-sm font-semibold">{t("navigation.operationen")}</h2>
        </header>
        <div className="space-y-1 p-2">
          {(["kontur", "tasche", "bohren", "gravur"] as OperationsTyp[]).map((typ) => (
            <button
              key={typ}
              className="block w-full rounded bg-camwosa-bg px-2 py-1 text-left text-xs hover:bg-gray-700 disabled:opacity-50"
              onClick={() => neueOperation(typ)}
              disabled={werkzeuge.length === 0}
            >
              + {OP_LABELS[typ]}
            </button>
          ))}
        </div>
        <ul className="border-t border-gray-700">
          {operationen.length === 0 && (
            <li className="px-3 py-2 text-xs text-camwosa-muted">
              Noch keine Operation angelegt
            </li>
          )}
          {operationen.map((op) => (
            <li
              key={op.id}
              className={clsx(
                "cursor-pointer border-b border-gray-800 px-3 py-2 text-xs",
                aktiveOpId === op.id
                  ? "bg-camwosa-accent/20 border-l-2 border-l-camwosa-accent"
                  : "hover:bg-camwosa-bg",
              )}
              onClick={() => setAktiveOpId(op.id)}
            >
              <div className="flex justify-between">
                <span className="font-medium">{op.name}</span>
                <span className="text-camwosa-muted">{OP_LABELS[op.typ]}</span>
              </div>
              <div className="mt-1 flex items-center gap-2">
                {op.toolpath && (
                  <span className="text-camwosa-ok">
                    ✓ {op.toolpath.bewegungen.length} Bew.
                  </span>
                )}
                {op.sicherheits_bericht?.hat_blocker && (
                  <span className="text-camwosa-danger">
                    ⚠ {op.sicherheits_bericht.anzahl_kritisch} kritisch
                  </span>
                )}
                {anzahlOverrides(op) > 0 && (
                  <span className="text-camwosa-accent">
                    {anzahlOverrides(op)} Override
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      </aside>

      {/* Editor rechts */}
      <main className="col-span-9 space-y-3">
        {!aktiveOp && (
          <div className="rounded border border-gray-700 bg-camwosa-surface p-6 text-sm text-camwosa-muted">
            Operation links auswaehlen oder neu anlegen.
          </div>
        )}

        {aktiveOp && (
          <>
            <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <input
                    className="rounded bg-camwosa-bg px-2 py-1 text-sm font-medium"
                    value={aktiveOp.name}
                    onChange={(e) =>
                      opAktualisieren(aktiveOp.id, { name: e.target.value })
                    }
                  />
                  <select
                    className="rounded bg-camwosa-bg px-2 py-1 text-xs"
                    value={aktiveOp.werkzeug_id}
                    onChange={(e) => {
                      opAktualisieren(aktiveOp.id, {
                        werkzeug_id: e.target.value,
                        parameter: {
                          ...(aktiveOp.parameter as unknown as Record<string, unknown>),
                          werkzeug_id: e.target.value,
                        } as unknown as KonturParameter,
                      });
                    }}
                  >
                    {werkzeuge.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <button
                    className="rounded border border-gray-600 px-3 py-1 text-xs text-camwosa-muted hover:text-white"
                    onClick={() => alleAufStandard(aktiveOp)}
                    title="Alle Overrides loeschen, Standardwerte verwenden"
                  >
                    ↺ Alle auf Standard
                  </button>
                  <button
                    className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
                    onClick={() => void berechnen(aktiveOp)}
                    disabled={berechneLaeuft}
                  >
                    {berechneLaeuft ? "Berechne..." : "Toolpath berechnen"}
                  </button>
                  <button
                    className="rounded border border-gray-600 px-3 py-1 text-xs text-camwosa-muted hover:text-camwosa-danger"
                    onClick={() => opLoeschen(aktiveOp.id)}
                  >
                    Loeschen
                  </button>
                </div>
              </div>
              {berechneFehler && (
                <div className="mt-2 rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
                  {berechneFehler}
                </div>
              )}
            </section>

            <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
              <h3 className="mb-2 text-sm font-semibold">
                Parameter
                <span className="ml-2 text-xs font-normal text-camwosa-muted">
                  Standardwerte aus Material-Preset · pro Feld ueberschreibbar
                </span>
              </h3>
              <OverrideOperationForm
                typ={aktiveOp.typ}
                werkzeugId={aktiveOp.werkzeug_id}
                materialId={aktivesMaterialId}
                overrides={aktiveOp.parameter as unknown as Record<string, unknown>}
                onChange={(p) =>
                  opAktualisieren(aktiveOp.id, {
                    parameter: p as unknown as KonturParameter,
                  })
                }
              />
            </section>

            <FeedsSpeedsPanel
              maschineId={maschine?.id ?? null}
              werkzeugId={aktiveOp.werkzeug_id}
              materialId={aktivesMaterialId}
            />

            {aktiveOp.sicherheits_bericht && (
              <SicherheitsZusammenfassung bericht={aktiveOp.sicherheits_bericht} />
            )}

            {aktiveOp.toolpath && <ToolpathStats toolpath={aktiveOp.toolpath} />}
          </>
        )}
      </main>
    </div>
  );
}

function anzahlOverrides(op: OperationEintrag): number {
  const p = op.parameter as unknown as Record<string, unknown>;
  // werkzeug_id ist Pflicht, zaehlt nicht als Override
  return Object.entries(p).filter(
    ([k, v]) => k !== "werkzeug_id" && v !== null && v !== undefined,
  ).length;
}

function ToolpathStats({ toolpath }: { toolpath: Toolpath }) {
  return (
    <section className="rounded border border-gray-700 bg-camwosa-surface p-3 text-sm">
      <h3 className="mb-2 font-semibold">Toolpath-Statistik</h3>
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <div className="text-camwosa-muted">Bewegungen</div>
          <div className="text-base font-mono">{toolpath.bewegungen.length}</div>
        </div>
        <div>
          <div className="text-camwosa-muted">Verfahrweg</div>
          <div className="text-base font-mono">
            {toolpath.gesamtlaenge?.toFixed(1) ?? "?"} mm
          </div>
        </div>
        <div>
          <div className="text-camwosa-muted">Schnittstrecke</div>
          <div className="text-base font-mono">
            {toolpath.schnittlaenge?.toFixed(1) ?? "?"} mm
          </div>
        </div>
      </div>
    </section>
  );
}

function SicherheitsZusammenfassung({ bericht }: { bericht: CheckBericht }) {
  return (
    <section
      className={clsx(
        "rounded border p-3 text-sm",
        bericht.hat_blocker
          ? "border-camwosa-danger bg-red-950/30"
          : bericht.anzahl_warnung > 0
          ? "border-camwosa-warn bg-yellow-950/20"
          : "border-camwosa-ok bg-green-950/20",
      )}
    >
      <h3 className="mb-2 font-semibold">
        Sicherheits-Pruefung:{" "}
        {bericht.hat_blocker
          ? "BLOCKIERT"
          : bericht.anzahl_warnung > 0
          ? "Warnungen"
          : "OK"}
      </h3>
      {bericht.ergebnisse.length === 0 && (
        <p className="text-xs text-camwosa-muted">Keine Probleme erkannt.</p>
      )}
      <ul className="space-y-1 text-xs">
        {bericht.ergebnisse.map((e, i) => (
          <li key={i}>
            <span
              className={clsx(
                "mr-1 font-semibold",
                e.stufe === "kritisch" && "text-camwosa-danger",
                e.stufe === "warnung" && "text-camwosa-warn",
                e.stufe === "info" && "text-camwosa-muted",
              )}
            >
              [{e.stufe}]
            </span>
            <strong>{e.titel}:</strong> {e.beschreibung}
          </li>
        ))}
      </ul>
    </section>
  );
}

function waehleGeometrie(
  op: OperationEintrag,
  geometrien: GeometrieObjekt[],
): GeometrieObjekt | null {
  if (geometrien.length === 0) return null;
  if (op.typ === "tasche") {
    return geometrien.find((g) => g.geschlossen) ?? null;
  }
  return geometrien[0];
}

function bohrpunkte(geometrien: GeometrieObjekt[]): Array<[number, number]> {
  const punkte: Array<[number, number]> = [];
  for (const g of geometrien) {
    if (g.typ === "kreis" || g.typ === "punkt") {
      punkte.push([g.punkte[0][0], g.punkte[0][1]]);
    }
  }
  return punkte;
}
