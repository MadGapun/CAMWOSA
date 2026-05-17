import { useEffect, useRef } from "react";
import * as THREE from "three";

interface Props {
  /** Pfad-Punkte in 2D (abgewickelt): [x_mm, y_mm] */
  punkte: Array<[number, number]>;
  werkstueck_radius_mm: number;
  /** Werkstueck-Laenge entlang X — wird aus den Punkten geschaetzt wenn 0 */
  werkstueck_laenge_mm?: number;
  hoehe?: number;
}

/**
 * Three.js-Preview: 2D-Pfad auf einen Zylinder gewickelt.
 *
 * Konvention:
 * - Werkstueck = Zylinder, Achse parallel zur CNC-X (= Three.js-X)
 * - Pfad-Punkte (x_mm, y_mm) werden auf die Zylinder-Oberflaeche projiziert:
 *     A = y / R Radiant
 *     X_3d = x
 *     Y_3d = R · cos(A)   (radial, Hoehe nach oben)
 *     Z_3d = R · sin(A)
 *
 * Werkzeug-Visualisierung: kleiner Kegel/Zylinder am letzten Pfad-Punkt
 * — vor Augen halten dass der Fraeser von oben auf den Zylinder zeigt.
 */
export default function WrapPreview3D({
  punkte, werkstueck_radius_mm, werkstueck_laenge_mm, hoehe = 320,
}: Props) {
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
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const dir = new THREE.DirectionalLight(0xffffff, 0.75);
    dir.position.set(100, 200, 200);
    scene.add(dir);

    const R = werkstueck_radius_mm;
    const xMax = werkstueck_laenge_mm
      ?? Math.max(50, ...punkte.map((p) => p[0])) * 1.2;
    const camera = new THREE.PerspectiveCamera(40, breite / hoehe, 0.1, 5000);

    // Zylinder (Werkstueck) — Drei.js Zylinder liegt entlang Y, wir drehen ihn
    // auf X-Achse: Rotation -90° um Z.
    const zylGeo = new THREE.CylinderGeometry(R, R, xMax, 64, 1, true);
    const zylMat = new THREE.MeshStandardMaterial({
      color: 0xb88a55, roughness: 0.6, side: THREE.DoubleSide, opacity: 0.6, transparent: true,
    });
    const zylMesh = new THREE.Mesh(zylGeo, zylMat);
    zylMesh.rotation.z = -Math.PI / 2;
    zylMesh.position.x = xMax / 2;
    scene.add(zylMesh);

    // Zylinder-Edges
    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.CylinderGeometry(R, R, xMax, 32, 1)),
      new THREE.LineBasicMaterial({ color: 0x6b4a2b, transparent: true, opacity: 0.4 }),
    );
    edges.rotation.z = -Math.PI / 2;
    edges.position.x = xMax / 2;
    scene.add(edges);

    // Gewickelter Pfad
    if (punkte.length >= 2) {
      const linePoints = punkte.map(([x, y]) => {
        const a = y / R;
        return new THREE.Vector3(
          x,
          R * Math.cos(a),
          R * Math.sin(a),
        );
      });
      const lineGeo = new THREE.BufferGeometry().setFromPoints(linePoints);
      const line = new THREE.Line(
        lineGeo,
        new THREE.LineBasicMaterial({ color: 0xff6b00, linewidth: 3 }),
      );
      scene.add(line);

      // Kleine Marker-Spheres an jedem Punkt — bessere Sichtbarkeit
      const markerGeo = new THREE.SphereGeometry(R * 0.025, 8, 8);
      const markerMat = new THREE.MeshBasicMaterial({ color: 0xff6b00 });
      for (const p of linePoints) {
        const m = new THREE.Mesh(markerGeo, markerMat);
        m.position.copy(p);
        scene.add(m);
      }

      // Werkzeug-Indikator am Ende des Pfads — kleiner Kegel von OBEN drauf zeigend
      const last = linePoints[linePoints.length - 1];
      const wzGeo = new THREE.ConeGeometry(R * 0.08, R * 0.4, 12);
      const wzMat = new THREE.MeshStandardMaterial({ color: 0x4A9EFF });
      const wzMesh = new THREE.Mesh(wzGeo, wzMat);
      // Cone zeigt von oben nach unten zum Pfad-Punkt
      wzMesh.position.set(last.x, last.y + R * 0.25, last.z);
      scene.add(wzMesh);
    }

    // Kamera-Setup mit Drag-Steuerung
    let yaw = 0.8;
    let pitch = 0.4;
    let radius = Math.max(xMax, R * 3) * 1.4;
    const target = new THREE.Vector3(xMax / 2, 0, 0);

    const updateCam = () => {
      camera.position.set(
        target.x + Math.cos(yaw) * Math.cos(pitch) * radius,
        Math.sin(pitch) * radius,
        target.z + Math.sin(yaw) * Math.cos(pitch) * radius,
      );
      camera.lookAt(target);
    };
    updateCam();

    let mouseDown = false;
    let lastX = 0;
    let lastY = 0;
    const onDown = (e: MouseEvent) => { mouseDown = true; lastX = e.clientX; lastY = e.clientY; };
    const onUp = () => { mouseDown = false; };
    const onMove = (e: MouseEvent) => {
      if (!mouseDown) return;
      yaw += (e.clientX - lastX) * 0.01;
      pitch = Math.max(-Math.PI / 2 + 0.1, Math.min(Math.PI / 2 - 0.1, pitch + (e.clientY - lastY) * 0.01));
      lastX = e.clientX; lastY = e.clientY;
      updateCam();
    };
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const step = e.shiftKey ? 0.03 : e.ctrlKey ? 0.25 : 0.10;
      const dir = e.deltaY > 0 ? 1 : -1;
      radius = Math.max(R * 1.2, Math.min(R * 12, radius * (1 + dir * step)));
      updateCam();
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
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [punkte, werkstueck_radius_mm, werkstueck_laenge_mm, hoehe]);

  return (
    <div
      ref={containerRef}
      className="overflow-hidden rounded border border-camwosa-default"
      style={{ height: hoehe }}
    />
  );
}
