/**
 * Toolpath-Stage: Konva-basierte 2D-Vorschau.
 *
 * Stellt Geometrien (gestrichelt Original + Toolpath farbig) dar.
 * - Eilgaenge gestrichelt grau
 * - Schnittbewegungen farbig je Operations-Typ
 * - Plunge-Punkte als Marker
 * - Werkzeug-Nullpunkt rot
 * - Markiertes Bewegungs-Segment hervorgehoben (fuer Klick-zur-Stelle aus Sicherheits-Panel)
 *
 * Zoom + Pan via Mausrad / Drag.
 */

import { useEffect, useRef, useState } from "react";
import { Stage, Layer, Line, Circle, Group, Rect } from "react-konva";
import type Konva from "konva";
import type {
  Bewegung,
  GeometrieObjekt,
  OperationsTyp,
  Toolpath,
} from "../api/types";

interface Props {
  width: number;
  height: number;
  toolpaths: Toolpath[];
  geometrien?: GeometrieObjekt[];
  rohmaterial?: { x: number; y: number; breite: number; hoehe: number };
  highlightedBewegung?: { toolpathIndex: number; bewegungIndex: number } | null;
}

const FARBEN: Record<OperationsTyp, string> = {
  kontur: "#ff6b00",
  tasche: "#00b3a4",
  bohren: "#ffc107",
  gravur: "#9b59b6",
  relief: "#3498db",
  eilgang: "#888",
};

export default function ToolpathStage({
  width,
  height,
  toolpaths,
  geometrien = [],
  rohmaterial,
  highlightedBewegung,
}: Props) {
  const stageRef = useRef<Konva.Stage>(null);
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: width / 2, y: height / 2 });

  // Beim ersten Render automatisch passend skalieren
  useEffect(() => {
    const bbox = berechneBBox(toolpaths, geometrien, rohmaterial);
    if (!bbox) return;
    const padding = 40;
    const sx = (width - 2 * padding) / Math.max(bbox.w, 1);
    const sy = (height - 2 * padding) / Math.max(bbox.h, 1);
    const s = Math.min(sx, sy, 5);
    setScale(s);
    // Mittelpunkt der BBox an Bildmitte
    const cx = bbox.x + bbox.w / 2;
    const cy = bbox.y + bbox.h / 2;
    setPos({ x: width / 2 - cx * s, y: height / 2 + cy * s });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toolpaths.length, geometrien.length, width, height, rohmaterial?.breite]);

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
    const newScale = Math.max(0.05, Math.min(50, oldScale * (1 + direction * 0.1)));
    setScale(newScale);
    setPos({
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y + mousePointTo.y * newScale,
    });
  }

  return (
    <div className="relative">
      <div className="absolute right-2 top-2 z-10 flex gap-1 rounded bg-camwosa-bg/80 p-1 text-xs">
        <button className="rounded px-2 py-0.5 hover:bg-gray-700"
                onClick={() => setScale(scale * 1.2)}>+</button>
        <button className="rounded px-2 py-0.5 hover:bg-gray-700"
                onClick={() => setScale(scale / 1.2)}>−</button>
        <button className="rounded px-2 py-0.5 hover:bg-gray-700"
                onClick={() => {
                  const bbox = berechneBBox(toolpaths, geometrien, rohmaterial);
                  if (!bbox) return;
                  const padding = 40;
                  const sx = (width - 2 * padding) / Math.max(bbox.w, 1);
                  const sy = (height - 2 * padding) / Math.max(bbox.h, 1);
                  const s = Math.min(sx, sy, 5);
                  setScale(s);
                  const cx = bbox.x + bbox.w / 2;
                  const cy = bbox.y + bbox.h / 2;
                  setPos({ x: width / 2 - cx * s, y: height / 2 + cy * s });
                }}>Fit</button>
        <span className="px-2 py-0.5 text-camwosa-muted">{(scale * 100).toFixed(0)}%</span>
      </div>

      <Stage
        ref={stageRef}
        width={width}
        height={height}
        draggable
        x={pos.x}
        y={pos.y}
        scaleX={scale}
        scaleY={-scale} // Y-Achse umdrehen (CAM: Y nach oben)
        onWheel={onWheel}
        onDragEnd={(e) => setPos({ x: e.target.x(), y: e.target.y() })}
        style={{ background: "#0e0e0e", cursor: "grab" }}
      >
        <Layer listening={false}>
          {/* Achsen */}
          <Line points={[-10000, 0, 10000, 0]} stroke="#333" strokeWidth={1 / scale} />
          <Line points={[0, -10000, 0, 10000]} stroke="#333" strokeWidth={1 / scale} />

          {/* Rohmaterial */}
          {rohmaterial && (
            <Rect
              x={rohmaterial.x}
              y={rohmaterial.y}
              width={rohmaterial.breite}
              height={rohmaterial.hoehe}
              stroke="#555"
              strokeWidth={1 / scale}
              dash={[5 / scale, 5 / scale]}
            />
          )}

          {/* DXF-Geometrien (gestrichelt grau) */}
          {geometrien.map((g, i) => (
            <GeometrieRender key={`g${i}`} geo={g} scale={scale} />
          ))}

          {/* Toolpaths */}
          {toolpaths.map((tp, ti) => (
            <ToolpathRender
              key={`tp${ti}`}
              tp={tp}
              scale={scale}
              farbe={FARBEN[tp.operation_typ] ?? "#fff"}
              highlight={
                highlightedBewegung?.toolpathIndex === ti
                  ? highlightedBewegung.bewegungIndex
                  : null
              }
            />
          ))}

          {/* Werkzeug-Nullpunkt */}
          <Circle x={0} y={0} radius={3 / scale} fill="#dc3545" />
        </Layer>
      </Stage>

      {/* Status unten */}
      <div className="absolute bottom-2 left-2 rounded bg-camwosa-bg/80 px-2 py-1 text-xs text-camwosa-muted">
        Mausrad: Zoom · Drag: Pan · Werkzeug-Nullpunkt rot
      </div>
    </div>
  );
}

function GeometrieRender({ geo, scale }: { geo: GeometrieObjekt; scale: number }) {
  const sw = 1 / scale;
  if (geo.typ === "linie" || geo.typ === "polylinie" || geo.typ === "spline") {
    const flat = geo.punkte.flatMap((p) => [p[0], p[1]]);
    if (geo.geschlossen && geo.punkte.length > 0) {
      flat.push(geo.punkte[0][0], geo.punkte[0][1]);
    }
    return (
      <Line points={flat} stroke="#666" strokeWidth={sw} dash={[2 / scale, 2 / scale]} />
    );
  }
  if (geo.typ === "kreis") {
    const r = (geo.attribute.radius as number) ?? 0;
    return (
      <Circle x={geo.punkte[0][0]} y={geo.punkte[0][1]} radius={r}
              stroke="#666" strokeWidth={sw} dash={[2 / scale, 2 / scale]} />
    );
  }
  if (geo.typ === "punkt") {
    return <Circle x={geo.punkte[0][0]} y={geo.punkte[0][1]} radius={1 / scale} fill="#aaa" />;
  }
  return null;
}

function ToolpathRender({
  tp, scale, farbe, highlight,
}: { tp: Toolpath; scale: number; farbe: string; highlight: number | null }) {
  const sw = 1 / scale;

  // Segmente nach Bewegungs-Typ aufteilen
  type Segment = { typ: "eilgang" | "schnitt"; pts: number[]; idxStart: number };
  const segmente: Segment[] = [];
  let aktuell: Segment | null = null;
  let prev = tp.bewegungen[0];

  tp.bewegungen.forEach((b, i) => {
    if (i === 0) return;
    const ist_eilgang = b.typ === "eilgang";
    const segTyp = ist_eilgang ? "eilgang" : "schnitt";
    if (!aktuell || aktuell.typ !== segTyp) {
      aktuell = { typ: segTyp, pts: [prev.x, prev.y], idxStart: i - 1 };
      segmente.push(aktuell);
    }
    aktuell.pts.push(b.x, b.y);
    prev = b;
  });

  return (
    <Group>
      {segmente.map((seg, i) => (
        <Line
          key={i}
          points={seg.pts}
          stroke={seg.typ === "eilgang" ? "#666" : farbe}
          strokeWidth={(seg.typ === "eilgang" ? 0.5 : 1.2) / scale}
          dash={seg.typ === "eilgang" ? [3 / scale, 3 / scale] : undefined}
          opacity={seg.typ === "eilgang" ? 0.6 : 1}
        />
      ))}
      {/* Plunge-Punkte */}
      {tp.bewegungen
        .map((b, i) => ({ b, i }))
        .filter(({ b }) => b.typ === "plunge")
        .map(({ b, i }) => (
          <Circle
            key={`pl${i}`}
            x={b.x}
            y={b.y}
            radius={2 / scale}
            fill={farbe}
            opacity={0.8}
          />
        ))}
      {/* Highlight markierte Bewegung */}
      {highlight !== null && highlight < tp.bewegungen.length && (
        <Circle
          x={tp.bewegungen[highlight].x}
          y={tp.bewegungen[highlight].y}
          radius={6 / scale}
          stroke="#dc3545"
          strokeWidth={2 / scale}
        />
      )}
    </Group>
  );
}

function berechneBBox(
  toolpaths: Toolpath[],
  geometrien: GeometrieObjekt[],
  rohmaterial?: { x: number; y: number; breite: number; hoehe: number },
): { x: number; y: number; w: number; h: number } | null {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  let leer = true;

  function add(x: number, y: number) {
    leer = false;
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }

  for (const g of geometrien) {
    if (g.typ === "kreis") {
      const r = (g.attribute.radius as number) ?? 0;
      add(g.punkte[0][0] - r, g.punkte[0][1] - r);
      add(g.punkte[0][0] + r, g.punkte[0][1] + r);
    } else {
      for (const p of g.punkte) add(p[0], p[1]);
    }
  }
  for (const tp of toolpaths) {
    for (const b of tp.bewegungen) add(b.x, b.y);
  }
  if (rohmaterial) {
    add(rohmaterial.x, rohmaterial.y);
    add(rohmaterial.x + rohmaterial.breite, rohmaterial.y + rohmaterial.hoehe);
  }
  if (leer) return null;
  return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}
