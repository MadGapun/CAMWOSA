import { useEffect, useRef } from "react";
import * as THREE from "three";

interface Props {
  /** Boundary-Voxel-Indizes (vom Backend) — Welt-Koord = idx × aufloesung_mm */
  boundaryVoxel: Array<[number, number, number]>;
  aufloesungMm: number;
  werkstueck: { laenge_x: number; breite_y: number; hoehe_z: number };
  hoehe?: number;
}

/**
 * Voxel-Preview mit Three.js InstancedMesh.
 *
 * Rendert die vom Backend gelieferten Boundary-Voxel als kleine Wuerfel —
 * eine GPU-Instance pro Voxel via `InstancedMesh`. Skaliert auf ca. 100k Voxel
 * fluessig auf einer integrierten GPU.
 *
 * Bei groesseren Modellen sollte das Backend hoehere `aufloesung_mm` waehlen
 * (groessere Voxel = weniger Stueck).
 */
export default function VoxelPreview3D({
  boundaryVoxel, aufloesungMm, werkstueck, hoehe = 400,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const breite = container.clientWidth;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(breite, hoehe);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060607);

    // Lichter
    scene.add(new THREE.AmbientLight(0xffffff, 0.45));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.75);
    dirLight.position.set(
      werkstueck.laenge_x * 1.5,
      werkstueck.hoehe_z * 3,
      werkstueck.breite_y * 1.5,
    );
    scene.add(dirLight);

    // Werkstueck-Bounding-Box als Wireframe
    const bbGeo = new THREE.BoxGeometry(
      werkstueck.laenge_x, werkstueck.hoehe_z, werkstueck.breite_y,
    );
    const bbEdges = new THREE.EdgesGeometry(bbGeo);
    const bbLine = new THREE.LineSegments(
      bbEdges,
      new THREE.LineBasicMaterial({ color: 0x444449 }),
    );
    bbLine.position.set(
      werkstueck.laenge_x / 2, werkstueck.hoehe_z / 2, werkstueck.breite_y / 2,
    );
    scene.add(bbLine);

    // Voxel als InstancedMesh
    if (boundaryVoxel.length > 0) {
      const geo = new THREE.BoxGeometry(aufloesungMm, aufloesungMm, aufloesungMm);
      const mat = new THREE.MeshStandardMaterial({
        color: 0xb88a55, roughness: 0.7, metalness: 0.05,
      });
      const mesh = new THREE.InstancedMesh(geo, mat, boundaryVoxel.length);
      const dummy = new THREE.Object3D();
      const color = new THREE.Color(0xb88a55);
      const oben = new THREE.Color(0xd0a070);  // helle Tönung für Top-Voxel
      // Wir variieren die Farbe minimal nach Hoehe, damit man Tiefe sieht
      mesh.instanceColor = new THREE.InstancedBufferAttribute(
        new Float32Array(boundaryVoxel.length * 3), 3,
      );
      const maxIz = Math.max(...boundaryVoxel.map((v) => v[2]), 1);
      for (let i = 0; i < boundaryVoxel.length; i++) {
        const [ix, iy, iz] = boundaryVoxel[i];
        dummy.position.set(
          (ix + 0.5) * aufloesungMm,
          (iz + 0.5) * aufloesungMm,    // Y oben in Three.js = Z im CAM
          (iy + 0.5) * aufloesungMm,
        );
        dummy.updateMatrix();
        mesh.setMatrixAt(i, dummy.matrix);

        // Farb-Variation nach Hoehe
        const t = iz / maxIz;
        const c = color.clone().lerp(oben, t * 0.6);
        mesh.instanceColor.setXYZ(i, c.r, c.g, c.b);
      }
      mesh.instanceMatrix.needsUpdate = true;
      mesh.instanceColor.needsUpdate = true;
      (mat as THREE.MeshStandardMaterial).vertexColors = true;
      scene.add(mesh);
    }

    // Boden-Gitter
    const grid = new THREE.GridHelper(
      Math.max(werkstueck.laenge_x, werkstueck.breite_y) * 1.5,
      Math.max(10, Math.round(werkstueck.laenge_x / 20)),
      0x292930, 0x1c1c21,
    );
    scene.add(grid);

    // Kamera
    const camera = new THREE.PerspectiveCamera(40, breite / hoehe, 0.1, 5000);
    const diag = Math.max(werkstueck.laenge_x, werkstueck.breite_y, werkstueck.hoehe_z);
    camera.position.set(diag * 1.5, diag * 1.2, diag * 1.5);
    camera.lookAt(werkstueck.laenge_x / 2, werkstueck.hoehe_z / 2, werkstueck.breite_y / 2);

    // Maus-Drag-Steuerung
    let mouseDown = false;
    let lastX = 0;
    let lastY = 0;
    let yaw = 0.7;
    let pitch = 0.5;
    let radius = diag * 2.2;

    const updateCam = () => {
      camera.position.set(
        werkstueck.laenge_x / 2 + Math.cos(yaw) * Math.cos(pitch) * radius,
        Math.sin(pitch) * radius + werkstueck.hoehe_z / 2,
        werkstueck.breite_y / 2 + Math.sin(yaw) * Math.cos(pitch) * radius,
      );
      camera.lookAt(
        werkstueck.laenge_x / 2, werkstueck.hoehe_z / 2, werkstueck.breite_y / 2,
      );
    };
    updateCam();

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
      radius = Math.max(diag * 0.2, Math.min(diag * 8, radius * (1 + dir * step)));
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
  }, [boundaryVoxel, aufloesungMm, werkstueck, hoehe]);

  return (
    <div
      ref={containerRef}
      className="overflow-hidden rounded border border-camwosa-default"
      style={{ height: hoehe }}
    />
  );
}
