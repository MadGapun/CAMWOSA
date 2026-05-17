/**
 * 3D-Materialabtrag-Simulation (vereinfacht).
 *
 * Stellt das Rohmaterial als Box dar, faehrt den Werkzeug-Path ab und
 * zeigt das Werkzeug an seiner aktuellen Position. Echtes Voxel-Abtragen
 * (Material-Volumen modifizieren) folgt in einer naechsten Iteration —
 * fuer den Anfang ist die Werkzeug-Bahn-Visualisierung wertvoll genug.
 */

import { Canvas } from "@react-three/fiber";
import { OrbitControls, Box, Line } from "@react-three/drei";
import { useEffect, useMemo, useState } from "react";
import type { Toolpath } from "../api/types";

interface Props {
  toolpaths: Toolpath[];
  rohmaterial?: { laenge: number; breite: number; hoehe: number };
  werkzeugDurchmesser?: number;
}

export default function Simulation3D({
  toolpaths, rohmaterial, werkzeugDurchmesser = 6,
}: Props) {
  const punkte = useMemo(() => {
    const alle: [number, number, number][] = [];
    for (const tp of toolpaths) {
      for (const b of tp.bewegungen) {
        alle.push([b.x, b.z, b.y]);  // Three.js: Y nach oben
      }
    }
    return alle;
  }, [toolpaths]);

  const [step, setStep] = useState(punkte.length);
  const [auto, setAuto] = useState(false);

  useEffect(() => {
    if (!auto) return;
    const t = setInterval(() => {
      setStep((s) => Math.min(s + 20, punkte.length));
    }, 50);
    return () => clearInterval(t);
  }, [auto, punkte.length]);

  useEffect(() => {
    setStep(punkte.length);
  }, [punkte.length]);

  const sichtbar = punkte.slice(0, step);
  const werkzeug = sichtbar[sichtbar.length - 1] ?? [0, 0, 0];

  const roh = rohmaterial ?? { laenge: 200, breite: 150, hoehe: 20 };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-xs">
        <button
          className="rounded border border-gray-600 px-2 py-1 hover:bg-gray-700"
          onClick={() => setAuto(!auto)}
        >
          {auto ? "⏸ Pause" : "▶ Play"}
        </button>
        <button
          className="rounded border border-gray-600 px-2 py-1 hover:bg-gray-700"
          onClick={() => setStep(0)}
        >
          ⏮
        </button>
        <input
          type="range"
          min={0}
          max={punkte.length}
          value={step}
          onChange={(e) => setStep(parseInt(e.target.value))}
          className="flex-1"
        />
        <span className="font-mono text-camwosa-muted">
          {step}/{punkte.length}
        </span>
      </div>
      <div className="h-[500px] overflow-hidden rounded border border-gray-700 bg-black">
        <Canvas camera={{ position: [200, 200, 200], fov: 50, near: 0.1, far: 5000 }}>
          <ambientLight intensity={0.4} />
          <directionalLight position={[100, 200, 100]} intensity={0.8} />
          {/* Weiter Zoom-Bereich: von 1 mm Entfernung (Detail-View) bis 3 m (Uebersicht) */}
          <OrbitControls
            minDistance={1}
            maxDistance={3000}
            zoomSpeed={1.2}
            enableDamping
            dampingFactor={0.08}
          />
          {/* Rohmaterial */}
          <Box
            args={[roh.laenge, roh.hoehe, roh.breite]}
            position={[roh.laenge / 2, -roh.hoehe / 2, roh.breite / 2]}
          >
            <meshStandardMaterial color="#8b5a2b" opacity={0.4} transparent />
          </Box>
          {/* Toolpath als Linie */}
          {sichtbar.length > 1 && (
            <Line points={sichtbar} color="#ff6b00" lineWidth={1} />
          )}
          {/* Werkzeug an aktueller Position */}
          {sichtbar.length > 0 && (
            <Box
              args={[werkzeugDurchmesser, 30, werkzeugDurchmesser]}
              position={[werkzeug[0], werkzeug[1] + 15, werkzeug[2]]}
            >
              <meshStandardMaterial color="#888" />
            </Box>
          )}
          {/* Achsen */}
          <axesHelper args={[50]} />
        </Canvas>
      </div>
      <p className="text-xs text-camwosa-muted">
        Vereinfachte 3D-Vorschau (Toolpath + Werkzeug). Voxel-Materialabtrag
        folgt in naechster Iteration. Maus: Rotieren / Zoomen / Pan.
      </p>
    </div>
  );
}
