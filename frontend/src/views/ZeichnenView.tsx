import { useEffect, useMemo, useRef, useState } from "react";
import { Stage, Layer, Line, Rect, Circle as KCircle, Group, Text as KText } from "react-konva";
import type Konva from "konva";
import clsx from "clsx";
import {
  neuesObjekt,
  snap,
  useDrawingStore,
  type ZeichenWerkzeug,
} from "../state/drawingStore";
import { useAppStore } from "../state/store";
import AnnotationenEditor, { type Annotation } from "../editor/AnnotationenEditor";
import type { KonturParameter, OperationEintrag, OperationsTyp } from "../api/types";

const QUICK_OPS: { typ: OperationsTyp; label: string; nurGeschlossen?: boolean; nurKreisPunkt?: boolean }[] = [
  { typ: "kontur", label: "+ Kontur" },
  { typ: "tasche", label: "+ Tasche", nurGeschlossen: true },
  { typ: "bohren", label: "+ Bohren", nurKreisPunkt: true },
  { typ: "gravur", label: "+ Gravur" },
  { typ: "relief", label: "+ Relief", nurGeschlossen: true },
];

function uniqId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
}

function typLabel(t: OperationsTyp): string {
  return ({
    kontur: "Kontur", tasche: "Tasche", bohren: "Bohren",
    gravur: "Gravur", relief: "Relief", eilgang: "Eilgang", drechseln: "Drechseln",
  } as Record<OperationsTyp, string>)[t];
}

const WERKZEUGE: { id: ZeichenWerkzeug; label: string; tooltip: string }[] = [
  { id: "auswahl", label: "✋", tooltip: "Auswahl / Pan" },
  { id: "linie", label: "／", tooltip: "Linie" },
  { id: "rechteck", label: "▭", tooltip: "Rechteck" },
  { id: "kreis", label: "◯", tooltip: "Kreis" },
  { id: "polygon", label: "⬠", tooltip: "Polygon (Klicks, Doppelklick beendet)" },
  { id: "punkt", label: "•", tooltip: "Punkt (Bohrposition)" },
];

export default function ZeichnenView() {
  const setGeometrien = useAppStore((s) => s.setGeometrien);
  const operationHinzufuegen = useAppStore((s) => s.operationHinzufuegen);
  const operationen = useAppStore((s) => s.operationen);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const [opErzeugungsHinweise, setOpErzeugungsHinweise] = useState<string[] | null>(null);
  const [quickHinweis, setQuickHinweis] = useState<string | null>(null);

  const werkzeug = useDrawingStore((s) => s.werkzeug);
  const setWerkzeug = useDrawingStore((s) => s.setWerkzeug);
  const objekte = useDrawingStore((s) => s.objekte);
  const hinzufuegen = useDrawingStore((s) => s.hinzufuegen);
  const ausgewaehlteId = useDrawingStore((s) => s.ausgewaehlteId);
  const setAusgewaehlt = useDrawingStore((s) => s.setAusgewaehlt);
  const loeschen = useDrawingStore((s) => s.loeschen);
  const alleLoeschen = useDrawingStore((s) => s.alle_loeschen);
  const snapGrid = useDrawingStore((s) => s.snap_grid);
  const setSnapGrid = useDrawingStore((s) => s.setSnapGrid);
  const annotationen = useDrawingStore((s) => s.annotationen);
  const annotationSetzen = useDrawingStore((s) => s.annotationSetzen);
  const annotationPickId = useDrawingStore((s) => s.annotationPickId);
  const setAnnotationPickId = useDrawingStore((s) => s.setAnnotationPickId);

  // Konva: Welt-Koordinaten anhand Stage-Transform aus Maus-Position rechnen
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [scale, setScale] = useState(2);
  const [pos, setPos] = useState({ x: 100, y: 500 });
  const [vorlaeufig, setVorlaeufig] = useState<{
    start: [number, number];
    aktuell: [number, number];
  } | null>(null);
  // Polygon: Liste der bisherigen Punkte
  const [polygonPunkte, setPolygonPunkte] = useState<Array<[number, number]>>([]);

  useEffect(() => {
    function fit() {
      if (!containerRef.current) return;
      const r = containerRef.current.getBoundingClientRect();
      setSize({ w: Math.floor(r.width), h: Math.max(500, window.innerHeight - 200) });
    }
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  function weltAusMaus(): [number, number] | null {
    const stage = stageRef.current;
    if (!stage) return null;
    const p = stage.getPointerPosition();
    if (!p) return null;
    // Achtung: scaleY ist negativ (Y nach oben).
    const wx = (p.x - pos.x) / scale;
    const wy = -(p.y - pos.y) / scale;
    return [snap(wx, snapGrid), snap(wy, snapGrid)];
  }

  function onMouseDown() {
    const w = weltAusMaus();
    if (!w) return;

    // Annotation-Pick-Modus: naechster Klick setzt x/y der ausgewaehlten Annotation
    if (annotationPickId) {
      annotationSetzen(
        annotationen.map((a) =>
          a.id === annotationPickId ? { ...a, x: w[0], y: w[1] } : a,
        ),
      );
      setAnnotationPickId(null);
      return;
    }

    if (werkzeug === "auswahl") {
      setAusgewaehlt(null);
      return;
    }

    if (werkzeug === "punkt") {
      const o = neuesObjekt("punkt");
      o.punkte = [w];
      hinzufuegen(o);
      return;
    }

    if (werkzeug === "polygon") {
      setPolygonPunkte((pts) => [...pts, w]);
      return;
    }

    setVorlaeufig({ start: w, aktuell: w });
  }

  function onMouseMove() {
    if (!vorlaeufig) return;
    const w = weltAusMaus();
    if (!w) return;
    setVorlaeufig({ ...vorlaeufig, aktuell: w });
  }

  function onMouseUp() {
    if (!vorlaeufig) return;
    const { start, aktuell } = vorlaeufig;
    setVorlaeufig(null);
    if (werkzeug === "linie") {
      const o = neuesObjekt("linie");
      o.punkte = [start, aktuell];
      hinzufuegen(o);
    } else if (werkzeug === "rechteck") {
      const [x1, y1] = start;
      const [x2, y2] = aktuell;
      const o = neuesObjekt("polylinie");
      o.punkte = [
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2],
      ];
      o.geschlossen = true;
      hinzufuegen(o);
    } else if (werkzeug === "kreis") {
      const dx = aktuell[0] - start[0];
      const dy = aktuell[1] - start[1];
      const r = Math.hypot(dx, dy);
      if (r < 0.001) return;
      const o = neuesObjekt("kreis");
      o.punkte = [start];
      o.geschlossen = true;
      o.attribute = { radius: r };
      hinzufuegen(o);
    }
  }

  function onDoubleClick() {
    if (werkzeug === "polygon" && polygonPunkte.length >= 3) {
      const o = neuesObjekt("polylinie");
      o.punkte = polygonPunkte;
      o.geschlossen = true;
      hinzufuegen(o);
      setPolygonPunkte([]);
    }
  }

  function uebernehmenAlsGeometrie() {
    // D31: IDs werden erhalten, damit ZeichenObjekte und Geometrien im Store
    // referenzierbar sind und Operationen darauf verlinken koennen.
    setGeometrien(objekte);
  }

  /**
   * D31: Quick-Create — direkt aus der Zeichnung eine Operation fuer das
   * ausgewaehlte Objekt anlegen. Stellt sicher dass die Geometrien im Store sind.
   */
  function quickOpAnlegen(typ: OperationsTyp) {
    if (!ausgewaehlteId) return;
    if (werkzeuge.length === 0) {
      setQuickHinweis("Bitte zuerst ein Werkzeug im Tab 'Werkzeuge' anlegen.");
      return;
    }
    // 1. Sicherstellen, dass alle Zeichenobjekte im Geometrie-Store sind
    setGeometrien(objekte);
    // 2. Op mit Verknuepfung auf das selektierte Objekt anlegen
    const wid = werkzeuge[0].id;
    const opCount = operationen.length;
    const op: OperationEintrag = {
      id: uniqId("op"),
      name: `${typLabel(typ)} ${opCount + 1}`,
      typ,
      werkzeug_id: wid,
      geometrie_id: null,
      geometrie_ids: [ausgewaehlteId],
      parameter: { werkzeug_id: wid } as unknown as KonturParameter,
      aktiviert: true,
    };
    operationHinzufuegen(op);
    setQuickHinweis(`✓ ${op.name} angelegt — wechsle zum Tab "Operationen" um Parameter zu setzen.`);
  }

  /**
   * Set aller Geometrie-IDs die mindestens von einer Operation referenziert werden.
   * Wird fuer farbliche Markierung (D31 Schritt 4) + Op-Badges in der Objekt-Liste verwendet.
   */
  const verknuepfteIds = useMemo(() => {
    const set = new Set<string>();
    for (const op of operationen) {
      for (const id of op.geometrie_ids ?? []) set.add(id);
      if (op.geometrie_id) set.add(op.geometrie_id);
    }
    return set;
  }, [operationen]);

  function opsFuer(id: string): OperationEintrag[] {
    return operationen.filter(
      (op) => (op.geometrie_ids ?? []).includes(id) || op.geometrie_id === id,
    );
  }

  const ausgewaehltesObjekt = objekte.find((o) => o.id === ausgewaehlteId) ?? null;

  function onWheel(e: Konva.KonvaEventObject<WheelEvent>) {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;
    const oldScale = scale;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    const mousePointTo = {
      x: (pointer.x - pos.x) / oldScale,
      y: -(pointer.y - pos.y) / oldScale,
    };
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const newScale = Math.max(0.1, Math.min(50, oldScale * (1 + direction * 0.1)));
    setScale(newScale);
    setPos({
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y + mousePointTo.y * newScale,
    });
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between pr-10">
        <h1 className="text-xl font-bold">Integriertes Zeichnen</h1>
        <div className="flex items-center gap-2 text-xs">
          <label>
            Snap-Grid:
            <input
              type="number"
              className="ml-1 w-16 rounded bg-camwosa-bg px-2 py-1"
              value={snapGrid}
              step={0.5}
              min={0}
              onChange={(e) => setSnapGrid(parseFloat(e.target.value) || 0)}
            />{" "}
            mm
          </label>
          <button
            className="rounded border border-gray-600 px-3 py-1 text-xs hover:bg-gray-700"
            onClick={alleLoeschen}
            disabled={objekte.length === 0}
          >
            Alle loeschen
          </button>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white disabled:opacity-50"
            onClick={uebernehmenAlsGeometrie}
            disabled={objekte.length === 0}
          >
            Als Geometrie uebernehmen
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* Werkzeug-Palette */}
        <aside className="col-span-1 space-y-1 rounded border border-gray-700 bg-camwosa-surface p-2">
          {WERKZEUGE.map((w) => (
            <button
              key={w.id}
              title={w.tooltip}
              className={clsx(
                "block w-full rounded px-2 py-2 text-center text-lg",
                werkzeug === w.id
                  ? "bg-camwosa-accent text-white"
                  : "hover:bg-gray-700",
              )}
              onClick={() => setWerkzeug(w.id)}
            >
              {w.label}
            </button>
          ))}
        </aside>

        {/* Stage */}
        <div
          className="col-span-9 overflow-hidden rounded border border-gray-700 bg-camwosa-surface"
          ref={containerRef}
        >
          <Stage
            ref={stageRef}
            width={size.w}
            height={size.h}
            x={pos.x}
            y={pos.y}
            scaleX={scale}
            scaleY={-scale}
            draggable={werkzeug === "auswahl"}
            onDragEnd={(e) => setPos({ x: e.target.x(), y: e.target.y() })}
            onWheel={onWheel}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
            onDblClick={onDoubleClick}
            style={{ background: "#0e0e0e", cursor: werkzeug === "auswahl" ? "grab" : "crosshair" }}
          >
            <Layer listening={false}>
              {/* Achsen */}
              <Line points={[-10000, 0, 10000, 0]} stroke="#333" strokeWidth={1 / scale} />
              <Line points={[0, -10000, 0, 10000]} stroke="#333" strokeWidth={1 / scale} />

              {/* Snap-Grid (nur in Naehe Origin sichtbar) */}
              {snapGrid > 0 && scale > 5 && (
                <GridLayer grid={snapGrid} scale={scale} pos={pos} size={size} />
              )}

              {/* Vorhandene Objekte */}
              {objekte.map((o) => (
                <ObjektShape
                  key={o.id}
                  obj={o}
                  scale={scale}
                  highlight={ausgewaehlteId === o.id}
                  verknuepft={verknuepfteIds.has(o.id)}
                  onClick={
                    werkzeug === "auswahl" ? () => setAusgewaehlt(o.id) : undefined
                  }
                />
              ))}

              {/* Vorlaeufige Linie / Rechteck / Kreis */}
              {vorlaeufig && werkzeug === "linie" && (
                <Line
                  points={[
                    vorlaeufig.start[0], vorlaeufig.start[1],
                    vorlaeufig.aktuell[0], vorlaeufig.aktuell[1],
                  ]}
                  stroke="#ff6b00"
                  strokeWidth={1.2 / scale}
                  dash={[3 / scale, 3 / scale]}
                />
              )}
              {vorlaeufig && werkzeug === "rechteck" && (
                <Rect
                  x={Math.min(vorlaeufig.start[0], vorlaeufig.aktuell[0])}
                  y={Math.min(vorlaeufig.start[1], vorlaeufig.aktuell[1])}
                  width={Math.abs(vorlaeufig.aktuell[0] - vorlaeufig.start[0])}
                  height={Math.abs(vorlaeufig.aktuell[1] - vorlaeufig.start[1])}
                  stroke="#ff6b00"
                  strokeWidth={1.2 / scale}
                  dash={[3 / scale, 3 / scale]}
                />
              )}
              {vorlaeufig && werkzeug === "kreis" && (
                <KCircle
                  x={vorlaeufig.start[0]}
                  y={vorlaeufig.start[1]}
                  radius={Math.hypot(
                    vorlaeufig.aktuell[0] - vorlaeufig.start[0],
                    vorlaeufig.aktuell[1] - vorlaeufig.start[1],
                  )}
                  stroke="#ff6b00"
                  strokeWidth={1.2 / scale}
                  dash={[3 / scale, 3 / scale]}
                />
              )}

              {/* Polygon im Bau */}
              {werkzeug === "polygon" && polygonPunkte.length > 0 && (
                <Group>
                  <Line
                    points={polygonPunkte.flat()}
                    stroke="#ff6b00"
                    strokeWidth={1.2 / scale}
                  />
                  {polygonPunkte.map((p, i) => (
                    <KCircle
                      key={i}
                      x={p[0]}
                      y={p[1]}
                      radius={2 / scale}
                      fill="#ff6b00"
                    />
                  ))}
                </Group>
              )}

              {/* Annotationen — Bohrungen / Refpunkte / Kommentare / Ausschnitte */}
              {annotationen.map((a) => (
                <AnnotationShape
                  key={a.id}
                  ann={a}
                  scale={scale}
                  highlight={annotationPickId === a.id}
                />
              ))}

              {/* Origin */}
              <KCircle x={0} y={0} radius={2 / scale} fill="#dc3545" />
            </Layer>
          </Stage>

          {/* Pick-Modus-Hinweis */}
          {annotationPickId && (
            <div className="absolute left-2 top-2 rounded border border-camwosa-accent bg-camwosa-accent-soft px-3 py-1.5 text-xs text-camwosa-accent">
              Klick im Canvas → setzt Position der Annotation ·{" "}
              <button
                className="underline"
                onClick={() => setAnnotationPickId(null)}
              >
                abbrechen
              </button>
            </div>
          )}
        </div>

        {/* Liste rechts */}
        <aside className="col-span-2 space-y-3">
          <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
            <h2 className="mb-2 text-sm font-semibold">
              Objekte ({objekte.length})
              {verknuepfteIds.size > 0 && (
                <span className="ml-2 text-[10px] font-normal text-[#3ad473]">
                  · {verknuepfteIds.size} verknuepft
                </span>
              )}
            </h2>
            <ul className="space-y-1 text-xs">
              {objekte.map((o) => {
                const ops = opsFuer(o.id);
                return (
                  <li
                    key={o.id}
                    className={clsx(
                      "flex items-center justify-between rounded px-2 py-1",
                      ausgewaehlteId === o.id
                        ? "bg-camwosa-accent/20"
                        : "hover:bg-camwosa-bg",
                    )}
                    onClick={() => setAusgewaehlt(o.id)}
                  >
                    <span className="flex items-center gap-1.5">
                      <span>
                        {o.typ}
                        {o.geschlossen ? " (geschlossen)" : ""}
                      </span>
                      {ops.length > 0 && (
                        <span
                          className="rounded bg-[#3ad473]/20 px-1.5 py-0.5 text-[10px] text-[#3ad473]"
                          title={ops.map((op) => op.name).join(", ")}
                        >
                          ↪ {ops.length}
                        </span>
                      )}
                    </span>
                    <button
                      className="text-camwosa-muted hover:text-camwosa-danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        loeschen(o.id);
                      }}
                    >
                      ×
                    </button>
                  </li>
                );
              })}
              {objekte.length === 0 && (
                <li className="text-camwosa-muted">Noch nichts gezeichnet</li>
              )}
            </ul>
          </section>

          {/* D31 Schritt 3: Quick-Create + Op-Liste fuer ausgewaehlte Geometrie */}
          {ausgewaehltesObjekt && (
            <section className="rounded border border-camwosa-accent/40 bg-camwosa-surface p-3">
              <h2 className="mb-2 text-sm font-semibold text-camwosa-accent">
                Ausgewaehlt: {ausgewaehltesObjekt.typ}
                {ausgewaehltesObjekt.geschlossen ? " (geschlossen)" : ""}
              </h2>
              {opsFuer(ausgewaehltesObjekt.id).length > 0 ? (
                <div className="mb-2">
                  <div className="mb-1 text-[10px] uppercase tracking-wide text-camwosa-muted">
                    Verknuepfte Operationen
                  </div>
                  <ul className="space-y-0.5 text-xs">
                    {opsFuer(ausgewaehltesObjekt.id).map((op) => (
                      <li key={op.id} className="rounded bg-camwosa-bg px-2 py-1">
                        <span className="font-medium">{op.name}</span>
                        <span className="ml-2 text-camwosa-muted">{typLabel(op.typ)}</span>
                        {op.toolpath && (
                          <span className="ml-2 text-camwosa-ok">✓ Toolpath</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="mb-2 text-xs text-camwosa-muted">
                  Noch keine Operation verknuepft.
                </p>
              )}
              <div className="mb-1 text-[10px] uppercase tracking-wide text-camwosa-muted">
                Schnell anlegen
              </div>
              <div className="flex flex-wrap gap-1">
                {QUICK_OPS.filter((q) => {
                  if (q.nurGeschlossen && !ausgewaehltesObjekt.geschlossen) return false;
                  if (q.nurKreisPunkt
                      && ausgewaehltesObjekt.typ !== "kreis"
                      && ausgewaehltesObjekt.typ !== "punkt") return false;
                  return true;
                }).map((q) => (
                  <button
                    key={q.typ}
                    type="button"
                    className="rounded border border-gray-600 bg-camwosa-bg px-2 py-1 text-xs hover:bg-camwosa-accent hover:text-white disabled:opacity-50"
                    onClick={() => quickOpAnlegen(q.typ)}
                    disabled={werkzeuge.length === 0}
                    title={
                      werkzeuge.length === 0
                        ? "Bitte zuerst ein Werkzeug anlegen"
                        : `Neue ${typLabel(q.typ)}-Operation mit dieser Geometrie`
                    }
                  >
                    {q.label}
                  </button>
                ))}
              </div>
              {quickHinweis && (
                <div className="mt-2 rounded border border-camwosa-ok bg-green-950/30 p-2 text-xs text-camwosa-ok">
                  {quickHinweis}{" "}
                  <button
                    type="button"
                    className="ml-2 underline"
                    onClick={() => setQuickHinweis(null)}
                  >
                    schliessen
                  </button>
                </div>
              )}
            </section>
          )}
          <section className="rounded border border-gray-700 bg-camwosa-surface p-3 text-xs text-camwosa-muted">
            <strong>Werkzeug:</strong>{" "}
            {WERKZEUGE.find((w) => w.id === werkzeug)?.tooltip}
            <br />
            <span>Polygon: Doppelklick beendet</span>
          </section>

          <section className="rounded border border-gray-700 bg-camwosa-surface p-3">
            <h2 className="mb-2 text-sm font-semibold">
              Annotationen ({annotationen.length})
              <span className="ml-2 text-[10px] font-normal text-camwosa-muted">
                Anschlagbohrungen, Refpunkte, ...
              </span>
            </h2>
            <AnnotationenEditor
              annotationen={annotationen}
              onChange={annotationSetzen}
              onPosWaehlen={(id) => setAnnotationPickId(id)}
              onOperationenErzeugt={(ops, hinweise) => {
                for (const op of ops) {
                  operationHinzufuegen({
                    id: op.id,
                    name: op.name,
                    typ: op.typ as "kontur" | "tasche" | "bohren" | "gravur" | "relief",
                    werkzeug_id: (op.parameter.werkzeug_id as string) ?? "",
                    geometrie_id: null,
                    parameter: op.parameter as any,
                    aktiviert: true,
                  });
                }
                setOpErzeugungsHinweise(hinweise);
              }}
            />
            {opErzeugungsHinweise !== null && (
              <div className="mt-2 rounded border border-camwosa-info bg-info-soft p-2 text-xs">
                <div className="mb-1 font-semibold text-camwosa-text">
                  ✓ Operationen erzeugt — siehe Tab „Operationen"
                </div>
                {opErzeugungsHinweise.length > 0 && (
                  <ul className="space-y-0.5 text-camwosa-muted">
                    {opErzeugungsHinweise.map((h, i) => (
                      <li key={i}>· {h}</li>
                    ))}
                  </ul>
                )}
                <button
                  className="mt-1 text-camwosa-accent underline"
                  onClick={() => setOpErzeugungsHinweise(null)}
                >
                  schliessen
                </button>
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}

function AnnotationShape({
  ann, scale, highlight,
}: { ann: Annotation; scale: number; highlight: boolean }) {
  const farbe = highlight ? "#FF6B00" : ICON_FARBE[ann.typ];
  const sw = (highlight ? 2 : 1) / scale;

  // Bohrung / Ausschnitt → Kreis mit Durchmesser
  if (ann.typ === "anschlagbohrung" || ann.typ === "ausschnitt") {
    const r = (ann.durchmesser_mm ?? 3) / 2;
    return (
      <Group>
        <KCircle
          x={ann.x} y={ann.y} radius={r}
          stroke={farbe} strokeWidth={sw}
          dash={ann.typ === "ausschnitt" ? [3 / scale, 3 / scale] : undefined}
        />
        {/* Fadenkreuz fuer Mittelpunkt */}
        <Line points={[ann.x - r * 1.3, ann.y, ann.x + r * 1.3, ann.y]}
              stroke={farbe} strokeWidth={sw} />
        <Line points={[ann.x, ann.y - r * 1.3, ann.x, ann.y + r * 1.3]}
              stroke={farbe} strokeWidth={sw} />
      </Group>
    );
  }
  // Refpunkt → kleines Kreuz
  if (ann.typ === "refpunkt") {
    const s = 3 / scale;
    return (
      <Group>
        <Line points={[ann.x - s, ann.y - s, ann.x + s, ann.y + s]}
              stroke={farbe} strokeWidth={sw} />
        <Line points={[ann.x - s, ann.y + s, ann.x + s, ann.y - s]}
              stroke={farbe} strokeWidth={sw} />
      </Group>
    );
  }
  // Kommentar → kleiner Punkt + Text-Label (nur wenn Zoom hoch genug)
  if (ann.typ === "kommentar") {
    return (
      <Group>
        <KCircle x={ann.x} y={ann.y} radius={1.5 / scale} fill={farbe} />
        {scale > 2 && ann.text && (
          <KText
            x={ann.x + 3 / scale} y={ann.y + 3 / scale}
            text={ann.text}
            fontSize={11 / scale}
            fill={farbe}
            // Konva Y ist gespiegelt; Text muss zurueckgespiegelt werden
            scaleY={-1}
          />
        )}
      </Group>
    );
  }
  return null;
}

const ICON_FARBE: Record<Annotation["typ"], string> = {
  anschlagbohrung: "#FFB800",
  refpunkt: "#4A9EFF",
  kommentar: "#A8A8B0",
  ausschnitt: "#B388FF",
};

function ObjektShape({
  obj,
  scale,
  highlight,
  verknuepft,
  onClick,
}: {
  obj: ReturnType<typeof useDrawingStore.getState>["objekte"][number];
  scale: number;
  highlight: boolean;
  verknuepft?: boolean;
  onClick?: () => void;
}) {
  // D31 Schritt 4: Verknuepfte Geometrien gruen, ausgewaehlte orange, Rest hellblau
  const stroke = highlight
    ? "#ff6b00"
    : verknuepft
    ? "#3ad473"
    : "#a8d2ff";
  const sw = (highlight ? 2 : verknuepft ? 1.5 : 1) / scale;
  if (obj.typ === "linie" || obj.typ === "polylinie") {
    const flat = obj.punkte.flat();
    if (obj.geschlossen && obj.punkte.length > 0) {
      flat.push(obj.punkte[0][0], obj.punkte[0][1]);
    }
    return <Line points={flat} stroke={stroke} strokeWidth={sw} onClick={onClick}
                 onTap={onClick} listening={!!onClick} />;
  }
  if (obj.typ === "kreis") {
    const r = (obj.attribute.radius as number) ?? 0;
    return (
      <KCircle
        x={obj.punkte[0][0]}
        y={obj.punkte[0][1]}
        radius={r}
        stroke={stroke}
        strokeWidth={sw}
        onClick={onClick}
        onTap={onClick}
        listening={!!onClick}
      />
    );
  }
  if (obj.typ === "punkt") {
    return (
      <KCircle
        x={obj.punkte[0][0]}
        y={obj.punkte[0][1]}
        radius={2 / scale}
        fill={stroke}
        onClick={onClick}
        onTap={onClick}
        listening={!!onClick}
      />
    );
  }
  return null;
}

function GridLayer({
  grid, scale, pos, size,
}: { grid: number; scale: number; pos: { x: number; y: number }; size: { w: number; h: number } }) {
  // Welt-Bereich des sichtbaren Stage-Fensters
  const wx0 = -pos.x / scale;
  const wx1 = (size.w - pos.x) / scale;
  const wy0 = (pos.y - size.h) / scale;
  const wy1 = pos.y / scale;
  const startX = Math.floor(wx0 / grid) * grid;
  const startY = Math.floor(wy0 / grid) * grid;
  const lines: JSX.Element[] = [];
  for (let x = startX; x <= wx1; x += grid) {
    lines.push(<Line key={`vx${x}`} points={[x, wy0, x, wy1]} stroke="#222" strokeWidth={0.3 / scale} />);
  }
  for (let y = startY; y <= wy1; y += grid) {
    lines.push(<Line key={`hy${y}`} points={[wx0, y, wx1, y]} stroke="#222" strokeWidth={0.3 / scale} />);
  }
  return <Group>{lines}</Group>;
}
