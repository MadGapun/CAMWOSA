import { useEffect, useRef, useState } from "react";
import { Stage, Layer, Line, Circle, Rect } from "react-konva";
import type Konva from "konva";
import * as THREE from "three";

export type ProfilPunkt = [number, number];  // [laenge_x_mm, radius_mm]

interface Props {
  profil: ProfilPunkt[];
  onChange: (p: ProfilPunkt[]) => void;
  rohmaterial_radius_mm: number;
  hoehe?: number;
}

/**
 * Drechsel-Profil-Editor.
 *
 * - Links: 2D-Halbschnitt (Konva). X waagerecht, Radius senkrecht.
 *   - Klick auf leere Stelle: neuer Punkt
 *   - Drag eines Punkts: verschiebt ihn (Snap auf 0.5mm)
 *   - Rechtsklick: Punkt loeschen
 * - Rechts: 3D-Revolution-Preview (Three.js Lathe-Geometrie um X-Achse).
 *
 * Profil-Konvention: aufsteigend in X, Radius ≥ 0 und ≤ rohmaterial_radius_mm.
 * Verstoesse werden visuell markiert (roter Punkt).
 */
export default function DrechselProfilEditor({
  profil, onChange, rohmaterial_radius_mm, hoehe = 320,
}: Props) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-camwosa-muted">
          <span>Halbschnitt</span>
          <span className="font-mono">{profil.length} Punkt(e)</span>
        </div>
        <ProfilCanvas2D
          profil={profil}
          onChange={onChange}
          rohmaterial_radius_mm={rohmaterial_radius_mm}
          hoehe={hoehe}
        />
        <p className="mt-1 text-[10px] text-camwosa-muted">
          Klick = neuer Punkt · Drag = verschieben · Rechtsklick = loeschen ·
          Snap auf 0.5 mm
        </p>
      </div>
      <div>
        <div className="mb-1 text-xs text-camwosa-muted">Revolution (3D)</div>
        <RevolutionPreview
          profil={profil}
          rohmaterial_radius_mm={rohmaterial_radius_mm}
          hoehe={hoehe}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2D-Profil-Editor (Konva)
// ---------------------------------------------------------------------------

function ProfilCanvas2D({
  profil, onChange, rohmaterial_radius_mm, hoehe,
}: {
  profil: ProfilPunkt[];
  onChange: (p: ProfilPunkt[]) => void;
  rohmaterial_radius_mm: number;
  hoehe: number;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [breite, setBreite] = useState(400);

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

  // Auto-Fit: Skala so dass Profil-X + Rohmaterial-Radius in Canvas passen
  const xMax = Math.max(100, ...profil.map((p) => p[0])) + 20;
  const rMax = Math.max(rohmaterial_radius_mm * 1.2, 30);
  const padding = 25;
  const sx = (breite - 2 * padding) / xMax;
  const sy = (hoehe - 2 * padding) / rMax;
  const scale = Math.min(sx, sy);

  function welt(p: { x: number; y: number }): ProfilPunkt {
    const x = (p.x - padding) / scale;
    const r = (hoehe - padding - p.y) / scale;
    return [Math.round(x * 2) / 2, Math.round(r * 2) / 2];  // Snap 0.5mm
  }

  function screen(x: number, r: number): { x: number; y: number } {
    return { x: padding + x * scale, y: hoehe - padding - r * scale };
  }

  function onClickCanvas(e: Konva.KonvaEventObject<MouseEvent>) {
    // Nur wenn auf leere Flaeche geklickt — Punkte handhaben sich selbst
    if (e.target !== e.target.getStage()) return;
    const pos = stageRef.current?.getPointerPosition();
    if (!pos) return;
    const [x, r] = welt(pos);
    if (x < 0 || r < 0) return;
    // Einfuegen so dass X aufsteigend bleibt
    const neu: ProfilPunkt[] = [...profil, [x, r]].sort((a, b) => a[0] - b[0]);
    onChange(neu);
  }

  function onDragMovePunkt(idx: number, e: Konva.KonvaEventObject<DragEvent>) {
    const node = e.target;
    const [x, r] = welt({ x: node.x(), y: node.y() });
    const sicher_r = Math.max(0, Math.min(rohmaterial_radius_mm, r));
    const sicher_x = Math.max(0, x);
    const neu = profil.map((p, i): ProfilPunkt =>
      i === idx ? [sicher_x, sicher_r] : p
    );
    // Re-sort wenn der gezogene Punkt jetzt nicht mehr aufsteigend ist
    onChange([...neu].sort((a, b) => a[0] - b[0]));
  }

  function onRechtsklickPunkt(idx: number, e: Konva.KonvaEventObject<MouseEvent>) {
    e.evt.preventDefault();
    onChange(profil.filter((_, i) => i !== idx));
  }

  const rohmat_y = hoehe - padding - rohmaterial_radius_mm * scale;

  return (
    <div ref={containerRef} className="overflow-hidden rounded border border-camwosa-default bg-camwosa-inset">
      <Stage
        ref={stageRef}
        width={breite}
        height={hoehe}
        onClick={onClickCanvas}
      >
        <Layer listening={false}>
          {/* Achse X (Werkstueck-Laengsachse) */}
          <Line
            points={[padding, hoehe - padding, breite - padding, hoehe - padding]}
            stroke="#3A3A44" strokeWidth={1}
          />
          {/* Y-Achse */}
          <Line
            points={[padding, padding, padding, hoehe - padding]}
            stroke="#3A3A44" strokeWidth={1}
          />
          {/* Rohmaterial-Radius als gestrichelte Linie */}
          <Line
            points={[padding, rohmat_y, breite - padding, rohmat_y]}
            stroke="#FFB800" strokeWidth={1} dash={[4, 4]} opacity={0.6}
          />
          {/* Werkstueck-Bereich als gelbes Rechteck zur Veranschaulichung */}
          <Rect
            x={padding} y={rohmat_y}
            width={breite - 2 * padding}
            height={hoehe - padding - rohmat_y}
            fill="#FFB800" opacity={0.05}
          />
        </Layer>

        <Layer>
          {/* Profil als zusammenhaengende Linie */}
          {profil.length >= 2 && (
            <Line
              points={profil.flatMap((p) => {
                const s = screen(p[0], p[1]);
                return [s.x, s.y];
              })}
              stroke="#FF6B00" strokeWidth={2}
            />
          )}
          {/* Punkte (drag/right-click) */}
          {profil.map(([x, r], idx) => {
            const s = screen(x, r);
            const invalid = r > rohmaterial_radius_mm + 0.001 || r < 0;
            return (
              <Circle
                key={`${idx}_${x}_${r}`}
                x={s.x}
                y={s.y}
                radius={6}
                fill={invalid ? "#FF453A" : "#FF6B00"}
                stroke="#F2F2F4"
                strokeWidth={1}
                draggable
                onDragMove={(e) => onDragMovePunkt(idx, e)}
                onDragEnd={(e) => onDragMovePunkt(idx, e)}
                onContextMenu={(e) => onRechtsklickPunkt(idx, e)}
              />
            );
          })}
        </Layer>
      </Stage>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 3D-Revolution-Preview (Three.js Lathe um X-Achse)
// ---------------------------------------------------------------------------

function RevolutionPreview({
  profil, rohmaterial_radius_mm, hoehe,
}: {
  profil: ProfilPunkt[];
  rohmaterial_radius_mm: number;
  hoehe: number;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const breite = container.clientWidth;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(breite, hoehe);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060607);

    const camera = new THREE.PerspectiveCamera(40, breite / hoehe, 0.1, 5000);
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.7);
    dirLight.position.set(100, 200, 200);
    scene.add(dirLight);

    if (profil.length >= 2) {
      // LatheGeometry rotiert um Y-Achse. Wir wollen um X-Achse rotieren —
      // also Profil als (Radius=y, X=x) übergeben und die ganze Mesh um -90°
      // um Z drehen, so dass die X-Achse waagerecht bleibt.
      const punkte = profil.map(
        ([x, r]) => new THREE.Vector2(r, x),  // (r, x) — wegen Lathe-Konvention
      );
      const geo = new THREE.LatheGeometry(punkte, 48);
      const mat = new THREE.MeshStandardMaterial({
        color: 0xb88a55, roughness: 0.6, metalness: 0.05, flatShading: false,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.z = -Math.PI / 2;  // damit X waagerecht
      scene.add(mesh);

      // Rohmaterial-Hinweis als Drahtmodell-Zylinder
      const rohGeo = new THREE.CylinderGeometry(
        rohmaterial_radius_mm, rohmaterial_radius_mm,
        Math.max(...profil.map((p) => p[0])) - Math.min(...profil.map((p) => p[0])),
        32, 1, true,
      );
      const rohMat = new THREE.MeshBasicMaterial({
        color: 0xffb800, wireframe: true, opacity: 0.15, transparent: true,
      });
      const rohMesh = new THREE.Mesh(rohGeo, rohMat);
      rohMesh.rotation.z = -Math.PI / 2;
      rohMesh.position.x = (Math.max(...profil.map((p) => p[0])) + Math.min(...profil.map((p) => p[0]))) / 2;
      scene.add(rohMesh);
    }

    // Kamera positionieren
    const xMax = Math.max(100, ...profil.map((p) => p[0]));
    const camDist = Math.max(xMax, rohmaterial_radius_mm * 4) * 1.3;
    camera.position.set(xMax / 2, rohmaterial_radius_mm * 1.5, camDist);
    camera.lookAt(xMax / 2, 0, 0);

    // Auto-Rotation um Werkstuecks-Achse
    let raf = 0;
    let angle = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      angle += 0.003;
      camera.position.set(
        xMax / 2 + Math.cos(angle) * camDist,
        rohmaterial_radius_mm * 1.5 + Math.sin(angle * 0.7) * rohmaterial_radius_mm,
        Math.sin(angle) * camDist,
      );
      camera.lookAt(xMax / 2, 0, 0);
      renderer.render(scene, camera);
    };
    tick();

    return () => {
      cancelAnimationFrame(raf);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [profil, rohmaterial_radius_mm, hoehe]);

  return (
    <div
      ref={containerRef}
      className="overflow-hidden rounded border border-camwosa-default"
      style={{ height: hoehe }}
    />
  );
}
