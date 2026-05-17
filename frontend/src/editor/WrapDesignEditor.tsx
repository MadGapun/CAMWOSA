import { useEffect, useRef, useState } from "react";
import { Stage, Layer, Line, Circle as KCircle, Rect, Text as KText } from "react-konva";
import type Konva from "konva";

export type WrapPunkt = [number, number];  // [x_mm (Laengsachse), y_mm (Bogenlaenge)]

interface Props {
  punkte: WrapPunkt[];
  onChange: (p: WrapPunkt[]) => void;
  werkstueck_radius_mm: number;
  hoehe?: number;
}

/**
 * Wrap-Design-Editor — 2D-Pfad in der abgewickelten Form.
 *
 * Konvention:
 * - X-Achse waagerecht = Werkstueck-Laengsachse (bleibt linear)
 * - Y-Achse senkrecht = Bogenlaenge auf dem Werkstueck-Umfang
 * - Bei Werkstueck mit Radius R ist der Umfang 2π·R — das Design sollte
 *   in Y nicht groesser sein, sonst wickelt es sich mehrfach um
 *
 * Bedienung:
 * - Klick auf leere Stelle: neuer Punkt am Pfad-Ende
 * - Drag eines Punktes: verschieben (Snap auf 0.5mm)
 * - Rechtsklick auf Punkt: loeschen
 *
 * Visualisierung:
 * - Umfang-Linie als gelb-gestrichelt (oben, bei Y = 2π·R)
 * - Vorlagen-Buttons fuer haeufige Designs (Schriftzug-Platzhalter, Spirale)
 */
export default function WrapDesignEditor({
  punkte, onChange, werkstueck_radius_mm, hoehe = 320,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [breite, setBreite] = useState(600);

  useEffect(() => {
    const onResize = () => {
      if (containerRef.current) {
        setBreite(containerRef.current.clientWidth);
      }
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const umfang = 2 * Math.PI * werkstueck_radius_mm;
  // Auto-Fit: zeige zumindest 1.2× max(X, umfang)
  const xMax = Math.max(100, ...punkte.map((p) => p[0])) + 20;
  const yMax = Math.max(umfang * 1.1, 30);
  const padding = 30;
  const sx = (breite - 2 * padding) / xMax;
  const sy = (hoehe - 2 * padding) / yMax;
  const scale = Math.min(sx, sy);

  function welt(p: { x: number; y: number }): WrapPunkt {
    const x = (p.x - padding) / scale;
    const y = (hoehe - padding - p.y) / scale;
    return [Math.round(x * 2) / 2, Math.round(y * 2) / 2];
  }
  function screen(x: number, y: number): { x: number; y: number } {
    return { x: padding + x * scale, y: hoehe - padding - y * scale };
  }

  function onClickCanvas(e: Konva.KonvaEventObject<MouseEvent>) {
    if (e.target !== e.target.getStage()) return;
    const pos = stageRef.current?.getPointerPosition();
    if (!pos) return;
    const [x, y] = welt(pos);
    if (x < 0 || y < 0) return;
    onChange([...punkte, [x, y]]);
  }

  function onDragMovePunkt(idx: number, e: Konva.KonvaEventObject<DragEvent>) {
    const node = e.target;
    const [x, y] = welt({ x: node.x(), y: node.y() });
    onChange(punkte.map((p, i): WrapPunkt =>
      i === idx ? [Math.max(0, x), Math.max(0, y)] : p
    ));
  }

  function onRechtsklick(idx: number, e: Konva.KonvaEventObject<MouseEvent>) {
    e.evt.preventDefault();
    onChange(punkte.filter((_, i) => i !== idx));
  }

  const umfang_y = hoehe - padding - umfang * scale;
  const yMaxInDesign = Math.max(0, ...punkte.map((p) => p[1]));
  const ueberlauf = yMaxInDesign > umfang + 0.001;

  return (
    <div ref={containerRef} className="overflow-hidden rounded border border-camwosa-default bg-camwosa-inset">
      <Stage
        ref={stageRef}
        width={breite}
        height={hoehe}
        onClick={onClickCanvas}
      >
        <Layer listening={false}>
          {/* Achsen */}
          <Line
            points={[padding, hoehe - padding, breite - padding, hoehe - padding]}
            stroke="#3A3A44" strokeWidth={1}
          />
          <Line
            points={[padding, padding, padding, hoehe - padding]}
            stroke="#3A3A44" strokeWidth={1}
          />
          {/* Umfang-Linie (Werkstueck-Umfang) */}
          <Line
            points={[padding, umfang_y, breite - padding, umfang_y]}
            stroke="#FFB800" strokeWidth={1} dash={[4, 4]} opacity={0.7}
          />
          <KText
            x={breite - padding - 80} y={umfang_y - 14}
            text={`Umfang: ${umfang.toFixed(1)}mm`}
            fontSize={10} fill="#FFB800"
          />
          {/* Bereich oberhalb Umfang als gelb-roetlich */}
          {ueberlauf && (
            <Rect
              x={padding} y={padding}
              width={breite - 2 * padding}
              height={Math.max(0, umfang_y - padding)}
              fill="#FF453A" opacity={0.08}
            />
          )}
          {/* Achsen-Labels */}
          <KText
            x={padding + 4} y={padding}
            text="Y (Bogenlaenge mm)"
            fontSize={10} fill="#6B6B73"
          />
          <KText
            x={breite - padding - 130} y={hoehe - padding - 14}
            text="X (Werkstueck-Laenge mm)"
            fontSize={10} fill="#6B6B73"
          />
        </Layer>

        <Layer>
          {/* Pfad */}
          {punkte.length >= 2 && (
            <Line
              points={punkte.flatMap(([x, y]) => {
                const s = screen(x, y);
                return [s.x, s.y];
              })}
              stroke="#FF6B00" strokeWidth={2}
            />
          )}
          {/* Punkte */}
          {punkte.map(([x, y], idx) => {
            const s = screen(x, y);
            const ueber = y > umfang + 0.001;
            return (
              <KCircle
                key={`${idx}_${x}_${y}`}
                x={s.x}
                y={s.y}
                radius={6}
                fill={ueber ? "#FF453A" : "#FF6B00"}
                stroke="#F2F2F4"
                strokeWidth={1}
                draggable
                onDragMove={(e) => onDragMovePunkt(idx, e)}
                onDragEnd={(e) => onDragMovePunkt(idx, e)}
                onContextMenu={(e) => onRechtsklick(idx, e)}
              />
            );
          })}
        </Layer>
      </Stage>
    </div>
  );
}
