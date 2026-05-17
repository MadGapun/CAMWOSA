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
import OperationPreview3D, { VorschauModusToggle, istHeavy } from "../components/OperationPreview3D";
import { useUIPrefs } from "../state/uiPrefs";

const OP_LABELS: Record<OperationsTyp, string> = {
  kontur: "Kontur",
  tasche: "Tasche",
  bohren: "Bohren",
  gravur: "Gravur",
  relief: "Relief",
  eilgang: "Eilgang",
  drechseln: "Drechseln",
};

/**
 * Operations-Typen die mindestens eine Geometrie brauchen (Master-Plan D31).
 * Bohren ist Spezialfall: nutzt automatisch alle KREIS/PUNKT-Objekte,
 * deshalb optional.
 */
const GEOMETRIE_PFLICHT: ReadonlyArray<OperationsTyp> = ["kontur", "tasche", "gravur", "relief"];

function geoLabel(g: GeometrieObjekt, idx: number): string {
  const r = (g.attribute?.radius as number | undefined);
  const extra =
    g.typ === "kreis" && r ? ` r=${r.toFixed(1)}mm` :
    g.typ === "punkt" ? "" :
    ` (${g.punkte.length}P${g.geschlossen ? ", geschl." : ""})`;
  return `${idx + 1}. ${g.typ}${extra}${g.layer && g.layer !== "0" ? ` · ${g.layer}` : ""}`;
}

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
  const aktiveOpBerechenbar = aktiveOp ? operationIstBerechenbar(aktiveOp, geometrien) : false;
  const aktiveOpPflichtFehlt =
    aktiveOp != null && !geometrieIstOptional(aktiveOp.typ) && !aktiveOpBerechenbar;

  function neueOperation(typ: OperationsTyp) {
    if (werkzeuge.length === 0) return;
    const wid = werkzeuge[0].id;
    // D31: bei nur einer passenden Geometrie sofort verknuepfen, sonst leer (User muss waehlen)
    const passende = passendeGeometrienFuerTyp(geometrien, typ);
    const vorbelegung = passende.length === 1 && passende[0].id ? [passende[0].id] : [];
    const op: OperationEintrag = {
      id: uniqId("op"),
      name: `${OP_LABELS[typ]} ${operationen.length + 1}`,
      typ,
      werkzeug_id: wid,
      geometrie_id: null,
      geometrie_ids: vorbelegung,
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
                    disabled={berechneLaeuft || !aktiveOpBerechenbar}
                    title={
                      aktiveOpPflichtFehlt
                        ? "Bitte zuerst eine Geometrie verknuepfen"
                        : !aktiveOpBerechenbar
                        ? "Keine passende Geometrie im Projekt vorhanden"
                        : "Toolpath aus aktuellen Parametern berechnen"
                    }
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

            <GeometrieAuswahl
              op={aktiveOp}
              geometrien={geometrien}
              onChange={(ids) => opAktualisieren(aktiveOp.id, { geometrie_ids: ids })}
            />

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

            <LivePreviewPanel op={aktiveOp} geometrien={geometrien} />

            {aktiveOp.toolpath && <ToolpathStats toolpath={aktiveOp.toolpath} />}
          </>
        )}
      </main>
    </div>
  );
}

/**
 * Live-3D-Vorschau der aktiven Operation — reagiert auf Parameter-Aenderungen
 * (max_tiefe, geometrie) ohne Toolpath-Berechnung.
 *
 * Wechselbar: Aus / Vereinfacht / Komplett. Default kommt aus UIPrefs,
 * pro Operation ueberschreibbar im Header. Bei „heavy" Vorschauen (viele
 * Punkte) gibt es einen Performance-Hint.
 */
function LivePreviewPanel({
  op, geometrien,
}: { op: OperationEintrag; geometrien: GeometrieObjekt[] }) {
  const standardModus = useUIPrefs((s) => s.vorschauModusDefault);
  const [override, setOverride] = useState<"aus" | "vereinfacht" | "komplett" | null>(null);
  const modus = override ?? standardModus;

  const p = op.parameter as unknown as Record<string, unknown>;
  const tiefe = typeof p.max_tiefe === "number" ? p.max_tiefe : 5;

  // Werkstueck-Defaults — wenn kein Projekt-Rohmaterial bekannt ist
  const werkstueck = { laenge: 200, breite: 200, hoehe: Math.max(tiefe + 2, 12) };

  // Vorschau aus der ersten passenden Geometrie ableiten
  const vorschau = useVorschau(op, geometrien, tiefe);
  const heavy = istHeavy(vorschau);

  return (
    <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          Live-Vorschau
          <span className="ml-2 text-xs font-normal text-camwosa-muted">
            reagiert auf Parameter-Aenderungen
          </span>
        </h3>
        <VorschauModusToggle
          modus={modus}
          onChange={(m) => setOverride(m)}
          hint={heavy ? 'viele Punkte — „Vereinfacht" empfohlen' : undefined}
        />
      </div>
      <OperationPreview3D
        werkstueck={werkstueck}
        vorschau={vorschau}
        modus={modus}
        hoehe={260}
      />
    </section>
  );
}

function useVorschau(
  op: OperationEintrag,
  geometrien: GeometrieObjekt[],
  tiefe: number,
):
  | { typ: "tasche"; breite: number; hoehe: number; tiefe: number; x?: number; y?: number }
  | { typ: "bohrloecher"; punkte: [number, number][]; tiefe: number; durchmesser: number }
  | { typ: "kontur"; pfad: [number, number][]; tiefe: number }
  | { typ: "gravur"; pfade: [number, number][][]; tiefe: number }
  | null
{
  // D31: Nutze explizit verknuepfte Geometrien wenn vorhanden, sonst Auto-Wahl
  const verknuepft = (op.geometrie_ids ?? []).length > 0
    ? geometrien.filter((g) => g.id && op.geometrie_ids!.includes(g.id))
    : null;
  const pool = verknuepft ?? geometrien;

  if (op.typ === "tasche") {
    const geo = pool.find((g) => g.geschlossen) ?? pool[0];
    if (!geo) return null;
    const bbox = bboxOf(geo);
    if (!bbox) return null;
    return {
      typ: "tasche", tiefe,
      breite: bbox.w, hoehe: bbox.h, x: bbox.x, y: bbox.y,
    };
  }
  if (op.typ === "bohren") {
    const punkte: [number, number][] = bohrpunkte(pool);
    if (!punkte.length) return null;
    // Werkzeug-Durchmesser zur Hand haben waere besser; fallback 3 mm.
    return { typ: "bohrloecher", punkte, tiefe, durchmesser: 3 };
  }
  if (op.typ === "kontur") {
    const geo = pool[0];
    if (!geo || geo.typ === "kreis" || geo.typ === "punkt") return null;
    return { typ: "kontur", pfad: geo.punkte as [number, number][], tiefe };
  }
  if (op.typ === "gravur") {
    const pfade: [number, number][][] = [];
    for (const g of pool) {
      if (g.typ !== "kreis" && g.typ !== "punkt") {
        pfade.push(g.punkte as [number, number][]);
      }
    }
    if (!pfade.length) return null;
    return { typ: "gravur", pfade, tiefe };
  }
  return null;
}

function bboxOf(geo: GeometrieObjekt): { x: number; y: number; w: number; h: number } | null {
  if (geo.typ === "kreis") {
    const r = (geo.attribute?.radius as number) ?? 0;
    return { x: geo.punkte[0][0] - r, y: geo.punkte[0][1] - r, w: r * 2, h: r * 2 };
  }
  if (!geo.punkte.length) return null;
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const [x, y] of geo.punkte) {
    if (x < minX) minX = x; if (y < minY) minY = y;
    if (x > maxX) maxX = x; if (y > maxY) maxY = y;
  }
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
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

/**
 * Geometrie-Verknuepfung fuer eine Operation (Master-Plan D31).
 * - Pflicht-Indikator wenn Typ Geometrie braucht aber keine ausgewaehlt ist
 * - Checkbox-Liste: Multi-Selektion (mehrere Konturen in einer Op)
 * - Filtert auf passende Typen (Tasche braucht geschlossen, Bohren nur Kreise/Punkte)
 * - "Alle"/"Keine"-Buttons fuer schnelle Auswahl
 */
function GeometrieAuswahl({
  op, geometrien, onChange,
}: {
  op: OperationEintrag;
  geometrien: GeometrieObjekt[];
  onChange: (ids: string[]) => void;
}) {
  const passend = passendeGeometrienFuerTyp(geometrien, op.typ);
  const aktuelle = op.geometrie_ids ?? (op.geometrie_id ? [op.geometrie_id] : []);
  const optional = geometrieIstOptional(op.typ);
  const fehltPflicht = !optional && aktuelle.length === 0;

  function toggle(id: string) {
    if (aktuelle.includes(id)) {
      onChange(aktuelle.filter((x) => x !== id));
    } else {
      onChange([...aktuelle, id]);
    }
  }

  return (
    <section
      className={clsx(
        "rounded border bg-camwosa-surface p-3",
        fehltPflicht ? "border-camwosa-warn" : "border-gray-700",
      )}
    >
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold">
          Geometrie-Verknuepfung
          {!optional && (
            <span className="ml-1 text-camwosa-danger" title="Pflichtfeld">
              *
            </span>
          )}
          <span className="ml-2 text-xs font-normal text-camwosa-muted">
            {op.typ === "bohren"
              ? "Bohrungen werden aus allen Kreisen/Punkten erzeugt"
              : op.typ === "tasche"
              ? "nur geschlossene Konturen erlaubt"
              : "welche Geometrien soll diese Operation verwenden"}
          </span>
        </h3>
        {passend.length > 1 && !optional && (
          <div className="flex gap-1 text-[10px]">
            <button
              type="button"
              className="rounded border border-gray-600 px-2 py-0.5 hover:bg-gray-700"
              onClick={() => onChange(passend.map((g) => g.id!).filter(Boolean))}
            >
              alle
            </button>
            <button
              type="button"
              className="rounded border border-gray-600 px-2 py-0.5 hover:bg-gray-700"
              onClick={() => onChange([])}
            >
              keine
            </button>
          </div>
        )}
      </div>

      {geometrien.length === 0 && (
        <p className="text-xs text-camwosa-muted">
          Noch keine Geometrien im Projekt. Importiere zuerst eine DXF-Datei oder zeichne im
          Tab "Zeichnen".
        </p>
      )}

      {geometrien.length > 0 && passend.length === 0 && (
        <p className="text-xs text-camwosa-warn">
          Keine passende Geometrie vorhanden ({op.typ === "tasche" ? "geschlossene Kontur" : op.typ === "bohren" ? "Kreis/Punkt" : "Linie/Polylinie/Kreis"} erforderlich).
        </p>
      )}

      {fehltPflicht && passend.length > 0 && (
        <p className="mb-2 text-xs text-camwosa-warn">
          ⚠ Bitte mindestens eine Geometrie auswaehlen — sonst kann kein Toolpath berechnet werden.
        </p>
      )}

      {passend.length > 0 && (
        <ul className="max-h-48 space-y-1 overflow-y-auto pr-1">
          {passend.map((g, i) => {
            const id = g.id ?? `__noid_${i}`;
            const checked = !!g.id && aktuelle.includes(g.id);
            return (
              <li key={id}>
                <label className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-xs hover:bg-camwosa-bg">
                  <input
                    type="checkbox"
                    className="accent-camwosa-accent"
                    checked={checked}
                    disabled={!g.id}
                    onChange={() => g.id && toggle(g.id)}
                  />
                  <span className={checked ? "font-medium text-camwosa-accent" : ""}>
                    {geoLabel(g, geometrien.indexOf(g))}
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function waehleGeometrie(
  op: OperationEintrag,
  geometrien: GeometrieObjekt[],
): GeometrieObjekt | null {
  // D31: Erst geometrie_ids (Multi), dann legacy geometrie_id, dann Auto-Fallback
  if (op.geometrie_ids && op.geometrie_ids.length > 0) {
    const treffer = geometrien.find((g) => g.id && op.geometrie_ids!.includes(g.id));
    if (treffer) return treffer;
  }
  if (op.geometrie_id) {
    const treffer = geometrien.find((g) => g.id === op.geometrie_id);
    if (treffer) return treffer;
  }
  // Auto-Fallback fuer Legacy-Operationen ohne Verknuepfung
  if (geometrien.length === 0) return null;
  if (op.typ === "tasche") {
    return geometrien.find((g) => g.geschlossen) ?? null;
  }
  return geometrien[0];
}

/**
 * Welche Geometrien passen technisch zu welchem Operations-Typ?
 * (Z.B. Tasche braucht geschlossene Kontur, Bohren nur Kreise/Punkte.)
 */
function passendeGeometrienFuerTyp(
  geometrien: GeometrieObjekt[],
  typ: OperationsTyp,
): GeometrieObjekt[] {
  if (typ === "tasche") return geometrien.filter((g) => g.geschlossen);
  if (typ === "bohren") return geometrien.filter((g) => g.typ === "kreis" || g.typ === "punkt");
  if (typ === "kontur" || typ === "gravur" || typ === "relief") {
    return geometrien.filter((g) => g.typ !== "punkt");
  }
  return geometrien;
}

/** True wenn fuer diese Operation eine Geometrie-Auswahl nicht erforderlich ist. */
function geometrieIstOptional(typ: OperationsTyp): boolean {
  return !GEOMETRIE_PFLICHT.includes(typ);
}

/** True wenn die Operation berechenbar ist (Geometrie-Verknuepfung erfuellt Pflicht). */
function operationIstBerechenbar(op: OperationEintrag, geometrien: GeometrieObjekt[]): boolean {
  if (geometrieIstOptional(op.typ)) {
    // Bohren: braucht zumindest passende Punkte/Kreise im Projekt
    if (op.typ === "bohren") {
      return geometrien.some((g) => g.typ === "kreis" || g.typ === "punkt");
    }
    return true;
  }
  // Pflicht-Geometrie via geometrie_ids ODER legacy geometrie_id
  if (op.geometrie_ids && op.geometrie_ids.length > 0) {
    return op.geometrie_ids.some((id) => geometrien.some((g) => g.id === id));
  }
  return !!op.geometrie_id && geometrien.some((g) => g.id === op.geometrie_id);
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
