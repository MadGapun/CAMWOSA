import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Leichte 3D-Vorschau einer einzelnen Operation auf einem Werkstueck.
 *
 * Drei Modi:
 * - **aus**: nur das Werkstueck (kein Overlay) — fuer schnelles Editieren
 *   ohne Render-Last, besonders bei komplexen Reliefs.
 * - **vereinfacht** (Default): Werkstueck halb-transparent + grobe Overlay-
 *   Geometrie (Tasche = Quader, Bohrloecher = Zylinder, Kontur = Linien).
 *   Reicht fuer „sehe ich Tiefe und Position?" — geht auch bei 1000+ Punkten.
 * - **komplett**: volles Overlay mit hoeher segmentierten Zylindern + Linien
 *   pro Pfad-Punkt. Spuerbar teurer bei Reliefs/Gravur.
 *
 * Wer pixelgenauen Material-Abtrag will, geht in die volle Simulation
 * (Simulation3DView) — die fuettert mit dem fertigen Toolpath.
 */

interface Werkstueck {
  laenge: number; // mm
  breite: number;
  hoehe: number;
}

type Vorschau =
  | {
    typ: "tasche";
    breite: number;
    hoehe: number;
    tiefe: number;
    x?: number; y?: number;
  }
  | {
    typ: "bohrloecher";
    punkte: Array<[number, number]>;
    tiefe: number;
    durchmesser: number;
  }
  | {
    typ: "kontur";
    pfad: Array<[number, number]>;
    tiefe: number;
  }
  | {
    typ: "gravur";
    pfade: Array<Array<[number, number]>>;
    tiefe: number;
  };

export type VorschauModus = "aus" | "vereinfacht" | "komplett";

interface Props {
  werkstueck: Werkstueck;
  vorschau: Vorschau | null;
  /** Hoehe in Pixel (Breite passt sich responsive an). */
  hoehe?: number;
  /** Render-Modus. Default: ``vereinfacht``. */
  modus?: VorschauModus;
}

/** Heuristik: ab wievielen Punkten gilt eine Vorschau als „heavy" und
 * profitiert von ``vereinfacht``? */
export function istHeavy(v: Vorschau | null): boolean {
  if (!v) return false;
  if (v.typ === "bohrloecher") return v.punkte.length > 50;
  if (v.typ === "gravur") {
    const ges = v.pfade.reduce((s, p) => s + p.length, 0);
    return ges > 200;
  }
  if (v.typ === "kontur") return v.pfad.length > 200;
  return false;
}

export default function OperationPreview3D({
  werkstueck, vorschau, hoehe = 280, modus = "vereinfacht",
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Modus „aus" — kein Overlay rendern, nur das Werkstueck.
    // Wir behandeln das, indem wir den vorschau-Wert weiter unten ignorieren.
    const effektiveVorschau = modus === "aus" ? null : vorschau;
    const detailMultiplier = modus === "komplett" ? 1 : 0.5;

    const breite = container.clientWidth;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(breite, hoehe);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e1118);

    const camera = new THREE.PerspectiveCamera(40, breite / hoehe, 0.1, 2000);
    const diag = Math.max(werkstueck.laenge, werkstueck.breite, werkstueck.hoehe);
    camera.position.set(diag * 1.2, diag * 1.2, diag * 1.5);
    camera.lookAt(werkstueck.laenge / 2, werkstueck.breite / 2, werkstueck.hoehe / 2);

    scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    const dir = new THREE.DirectionalLight(0xffffff, 0.7);
    dir.position.set(diag, diag * 1.5, diag);
    scene.add(dir);

    // Werkstueck — halbtransparente Holzfarbe
    const wsGeo = new THREE.BoxGeometry(
      werkstueck.laenge, werkstueck.hoehe, werkstueck.breite,
    );
    const wsMat = new THREE.MeshStandardMaterial({
      color: 0xb88a55, transparent: true, opacity: 0.55,
    });
    const werkstueckMesh = new THREE.Mesh(wsGeo, wsMat);
    werkstueckMesh.position.set(
      werkstueck.laenge / 2, werkstueck.hoehe / 2, werkstueck.breite / 2,
    );
    scene.add(werkstueckMesh);

    // Edges fuer bessere Sichtbarkeit
    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(wsGeo),
      new THREE.LineBasicMaterial({ color: 0x6b4a2b }),
    );
    edges.position.copy(werkstueckMesh.position);
    scene.add(edges);

    // Vorschau
    if (effektiveVorschau) {
      const vorschau = effektiveVorschau;
      switch (vorschau.typ) {
        case "tasche": {
          const x = vorschau.x ?? werkstueck.laenge / 2 - vorschau.breite / 2;
          const y = vorschau.y ?? werkstueck.breite / 2 - vorschau.hoehe / 2;
          const geo = new THREE.BoxGeometry(
            vorschau.breite, vorschau.tiefe, vorschau.hoehe,
          );
          const mat = new THREE.MeshStandardMaterial({
            color: 0x1f2733, transparent: true, opacity: 0.85,
          });
          const m = new THREE.Mesh(geo, mat);
          m.position.set(
            x + vorschau.breite / 2,
            werkstueck.hoehe - vorschau.tiefe / 2,
            y + vorschau.hoehe / 2,
          );
          scene.add(m);
          break;
        }
        case "bohrloecher": {
          const segs = Math.max(8, Math.round(24 * detailMultiplier));
          // In ``vereinfacht``: bei vielen Bohrloechern wird auf Punkte
          // reduziert (kein Voll-Zylinder pro Loch).
          const alsPunkt = modus === "vereinfacht" && vorschau.punkte.length > 80;
          if (alsPunkt) {
            const geo = new THREE.BufferGeometry().setFromPoints(
              vorschau.punkte.map(([px, py]) =>
                new THREE.Vector3(px, werkstueck.hoehe - vorschau.tiefe + 0.05, py),
              ),
            );
            const pts = new THREE.Points(
              geo,
              new THREE.PointsMaterial({ color: 0xff9966, size: vorschau.durchmesser }),
            );
            scene.add(pts);
            break;
          }
          for (const [px, py] of vorschau.punkte) {
            const geo = new THREE.CylinderGeometry(
              vorschau.durchmesser / 2, vorschau.durchmesser / 2,
              vorschau.tiefe, segs,
            );
            const m = new THREE.Mesh(
              geo,
              new THREE.MeshStandardMaterial({ color: 0x222933 }),
            );
            m.position.set(
              px, werkstueck.hoehe - vorschau.tiefe / 2, py,
            );
            scene.add(m);
          }
          break;
        }
        case "kontur":
        case "gravur": {
          let pfade = vorschau.typ === "kontur" ? [vorschau.pfad] : vorschau.pfade;
          // ``vereinfacht``: jeden 2. Punkt droppen wenn die Pfade dicht sind
          if (modus === "vereinfacht") {
            pfade = pfade.map((p) =>
              p.length > 100 ? p.filter((_, i) => i % 2 === 0) : p,
            );
          }
          for (const pfad of pfade) {
            if (pfad.length < 2) continue;
            const pts = pfad.map(([x, y]) =>
              new THREE.Vector3(x, werkstueck.hoehe - vorschau.tiefe + 0.05, y),
            );
            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            const line = new THREE.Line(
              geo,
              new THREE.LineBasicMaterial({
                color: vorschau.typ === "gravur" ? 0x60a5fa : 0xff9966,
                linewidth: 2,
              }),
            );
            scene.add(line);
          }
          break;
        }
      }
    }

    // Auto-Rotation als Default — User kann mit Mausziehen drehen
    let mouseDown = false;
    let lastX = 0;
    let yaw = 0.6;
    let pitch = 0.6;
    let radius = diag * 2.2;

    const updateKamera = () => {
      camera.position.set(
        werkstueck.laenge / 2 + Math.cos(yaw) * Math.cos(pitch) * radius,
        Math.sin(pitch) * radius + werkstueck.hoehe / 2,
        werkstueck.breite / 2 + Math.sin(yaw) * Math.cos(pitch) * radius,
      );
      camera.lookAt(werkstueck.laenge / 2, werkstueck.hoehe / 2, werkstueck.breite / 2);
    };
    updateKamera();

    const onDown = (e: MouseEvent) => { mouseDown = true; lastX = e.clientX; };
    const onUp = () => { mouseDown = false; };
    const onMove = (e: MouseEvent) => {
      if (!mouseDown) return;
      yaw += (e.clientX - lastX) * 0.01;
      lastX = e.clientX;
      updateKamera();
    };
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      // Weiter Zoom-Bereich: 0.1× bis 10× der Werkstueck-Diagonale.
      // Faktor-basiert (multiplikativ) statt linear — damit fuehlt sich Zoom
      // bei nahem und weitem Stand gleich an.
      const step = e.shiftKey ? 0.02 : e.ctrlKey ? 0.25 : 0.10;
      const dir = e.deltaY > 0 ? 1 : -1;
      const ratio = 1 + dir * step;
      radius = Math.max(diag * 0.1, Math.min(diag * 10, radius * ratio));
      updateKamera();
    };
    renderer.domElement.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("mousemove", onMove);
    renderer.domElement.addEventListener("wheel", onWheel, { passive: false });

    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      renderer.render(scene, camera);
    };
    tick();

    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      renderer.setSize(w, hoehe);
      camera.aspect = w / hoehe;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      renderer.domElement.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("mousemove", onMove);
      renderer.domElement.removeEventListener("wheel", onWheel);
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, [werkstueck, vorschau, hoehe, modus]);

  return <div ref={containerRef} className="w-full overflow-hidden rounded border border-gray-700" />;
}

/**
 * Toggle-Bar fuer die drei Vorschau-Modi. Reagiert auf Klick mit Callback.
 * Wird typischerweise im Preview-Header platziert.
 */
export function VorschauModusToggle({
  modus, onChange, hint,
}: {
  modus: VorschauModus;
  onChange: (m: VorschauModus) => void;
  hint?: string;
}) {
  const opts: Array<{ id: VorschauModus; label: string; titel: string }> = [
    { id: "aus", label: "Aus", titel: "Kein Overlay — nur Werkstueck" },
    { id: "vereinfacht", label: "Vereinfacht", titel: "Schnell, reduzierte Detailtiefe" },
    { id: "komplett", label: "Komplett", titel: "Voll, kann bei Relief langsam sein" },
  ];
  return (
    <div className="flex items-center gap-1 text-xs">
      <span className="text-camwosa-muted">Vorschau:</span>
      <div className="flex rounded border border-gray-700 bg-camwosa-surface">
        {opts.map((o) => (
          <button
            key={o.id}
            title={o.titel}
            onClick={() => onChange(o.id)}
            className={[
              "px-2 py-0.5 text-xs transition",
              modus === o.id
                ? "bg-camwosa-accent text-camwosa-bg"
                : "text-camwosa-text hover:bg-gray-700",
            ].join(" ")}
          >
            {o.label}
          </button>
        ))}
      </div>
      {hint && <span className="ml-1 text-[10px] text-camwosa-muted">{hint}</span>}
    </div>
  );
}
