import { useEffect, useRef } from "react";

interface Props {
  /** Float32-Z-Werte aus dem Backend (base64-dekodiert). */
  zValues: Float32Array;
  shape: [number, number];   // [nx, ny] — wie vom Backend
  maxTiefeMm: number;        // fuer Kontrast-Normalisierung
  hoehe?: number;            // Canvas-Hoehe in Pixel
}

/**
 * 2D-Grayscale-Preview einer Heightmap.
 *
 * Z-Werte werden auf 0..255 normalisiert (0 = max Tiefe = schwarz,
 * 0 = Oberflaeche = weiss). Pixel-genau, schnell, kein Three.js noetig.
 */
export default function HeightmapPreview({
  zValues, shape, maxTiefeMm, hoehe = 320,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const [nx, ny] = shape;
    if (!nx || !ny || zValues.length !== nx * ny) return;

    // Canvas auf Pixel-Maße setzen, CSS skaliert proportional auf hoehe
    canvas.width = nx;
    canvas.height = ny;
    const aspect = nx / ny;
    canvas.style.width = `${Math.round(hoehe * aspect)}px`;
    canvas.style.height = `${hoehe}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const img = ctx.createImageData(nx, ny);

    // Heightmap-Layout ist (x, y) = (i*ny + j). Pillow speichert pro Zeile
    // — wir laden Z[ix][iy] und schreiben Pixel an Position (ix, ny-1-iy)
    // damit der visuelle Bild-„oben" der hoechste Y-Wert ist.
    for (let ix = 0; ix < nx; ix++) {
      for (let iy = 0; iy < ny; iy++) {
        const z = zValues[ix * ny + iy];
        // 0 = Oberflaeche → 255 weiss. -maxTiefeMm = tief → 0 schwarz.
        const norm = Math.max(0, Math.min(1, 1 + z / Math.max(maxTiefeMm, 0.001)));
        const v = Math.round(norm * 255);
        const px = ix + (ny - 1 - iy) * nx;
        const idx = px * 4;
        img.data[idx + 0] = v;
        img.data[idx + 1] = v;
        img.data[idx + 2] = v;
        img.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [zValues, shape, maxTiefeMm, hoehe]);

  return (
    <div className="flex items-center justify-center overflow-hidden rounded border border-camwosa-default bg-camwosa-inset" style={{ height: hoehe }}>
      <canvas ref={canvasRef} style={{ imageRendering: "pixelated" }} />
    </div>
  );
}

/** Dekodiert das base64-z_values aus der API in Float32Array. */
export function dekodiereZValues(base64: string): Float32Array {
  const bin = atob(base64);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return new Float32Array(buf.buffer);
}
