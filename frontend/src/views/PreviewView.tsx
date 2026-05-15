import { Stage, Layer, Rect, Line, Circle } from "react-konva";
import { useTranslation } from "react-i18next";

/**
 * 2D-Toolpath-Vorschau (Konva).
 *
 * Phase 1: Statisches Beispiel zeigt die Komponenten. Datenbindung an
 * Toolpath-API folgt mit Operations-Editor.
 */
export default function PreviewView() {
  const { t } = useTranslation();
  return (
    <div className="space-y-2">
      <h1 className="text-xl font-bold">{t("navigation.preview")}</h1>
      <div className="rounded border border-gray-700 bg-camwosa-surface p-2">
        <Stage width={900} height={600}>
          <Layer>
            {/* Rohmaterial */}
            <Rect x={50} y={50} width={400} height={300} stroke="#666" strokeWidth={1} />
            {/* Beispiel-Toolpath */}
            <Line
              points={[80, 80, 400, 80, 400, 320, 80, 320, 80, 80]}
              stroke="#ff6b00"
              strokeWidth={2}
            />
            {/* Eilbewegung gestrichelt */}
            <Line points={[0, 0, 80, 80]} stroke="#888" strokeWidth={1} dash={[5, 5]} />
            {/* Werkzeug-Nullpunkt */}
            <Circle x={80} y={80} radius={4} fill="#dc3545" />
          </Layer>
        </Stage>
      </div>
      <p className="text-xs text-camwosa-muted">
        Beispiel-Anzeige — Toolpath wird live gerendert sobald Operations gespeichert sind.
      </p>
    </div>
  );
}
