# Material-Abtrag-Simulation (Voxel)

> **Status:** ✅ Backend (numpy-Voxel-Grid + Werkzeug-Stempel) + API + Frontend + MCP.
> **Code:** [backend/camwosa/cam/simulation.py](../../backend/camwosa/cam/simulation.py) · [frontend/src/views/MaterialAbtragView.tsx](../../frontend/src/views/MaterialAbtragView.tsx) · [components/VoxelPreview3D.tsx](../../frontend/src/components/VoxelPreview3D.tsx)
> **API:** `POST /api/simulation/voxel` · **MCP:** `material_abtrag_simulieren`
> **Tests:** [test_simulation.py](../../backend/tests/cam/test_simulation.py), [test_simulation_api.py](../../backend/tests/api/test_simulation_api.py)

Zeigt das Werkstueck **nach** dem CNC-Job — was vom Material uebrig bleibt. Im Gegensatz zur leichten `Simulation3D`-View (nur Toolpath-Linien) ist das die echte „so sieht's hinterher aus"-Vorschau.

## Algorithmus

1. **Werkstueck als 3D-Boolean-Grid** (`numpy.ndarray`): jeder Voxel ist „Material vorhanden" oder nicht.
2. **Toolpath durchlaufen**: jede Bewegung wird in feine Schritte aufgeteilt (Schrittweite < halbe Werkzeug-Radius).
3. **Werkzeug-Stempel pro Schritt**: alle Voxel im Werkzeug-Volumen (Spitze + Schaft) werden auf False gesetzt. Werkzeug-Radius variiert mit Z (nutzt das Segment-Modell aus dem Werkzeug-Profil).
4. **Surface-Extraktion**: nur die Voxel mit mindestens einem leeren Nachbarn werden ans Frontend gesendet. Innere Voxel sind unsichtbar — reduziert die Datenmenge um Faktor 10–100×.

## Bewusst KEIN echtes CSG (Mesh-Boolean)

- Voxel ist **robust** gegen selbst-schneidende Pfade, sehr feine Toolpath-Schritte, etc.
- Performant in numpy (vektorisierbar)
- Aufloesungs-skalierbar — User waehlt grob/fein nach Compute-Budget

## Voxel-Anzahl + Aufloesung

| Werkstueck | Aufloesung | Voxel-Anzahl | Bewertung |
|-----------|-----------|--------------|-----------|
| 200×200×20 mm | 2.0 mm | 100k | leicht |
| 400×400×30 mm | 2.0 mm | 1.2 Mio | OK |
| 400×400×100 mm | 2.0 mm | 4 Mio | grenzwertig |
| 400×400×100 mm | 1.0 mm | 16 Mio | zu schwer |

Frontend zeigt ab >5 Mio Voxel eine Warnung „heavy — groessere Aufloesung waehlen".

Boundary-Voxel sind viel weniger als Voll-Voxel:
- Ein 10×10×10-Quader hat 1000 Voll-Voxel, aber nur ~488 Boundary-Voxel
- Bei einer fertigen Tasche ist die Boundary-Voxel-Zahl typischerweise 5-20% der Voll-Anzahl

## Multi-Toolpath-Verkettung

`simuliere_toolpaths(...)` (Plural) nimmt eine Liste und arbeitet sie auf demselben Grid ab — ideal fuer Schruppen+Schlichten in einem Aufruf. Der Abtrag des ersten Werkzeugs bleibt fuer das zweite erhalten.

## API

```json
POST /api/simulation/voxel
{
  "werkzeug_id": "schaft_6mm_2s_hm",
  "toolpaths": [/* Liste von Toolpath-Dicts */],
  "werkstueck": {
    "laenge_x": 200, "breite_y": 200, "hoehe_z": 20
  },
  "aufloesung_mm": 2.0
}
```

Antwort:
```json
{
  "aufloesung_mm": 2.0,
  "nx": 100, "ny": 100, "nz": 10,
  "werkstueck": {...},
  "boundary_voxel": [[0,0,9], [1,0,9], ...],
  "voxel_count": 18532,
  "voxel_volumen_mm3": 798400,
  "abgetragenes_volumen_mm3": 1600,
  "bewegungen_simuliert": 412
}
```

## Frontend-Rendering

[VoxelPreview3D](../../frontend/src/components/VoxelPreview3D.tsx) rendert die Voxel als Three.js `InstancedMesh` — eine GPU-Instance pro Voxel. Skaliert auf ca. 100k Voxel fluessig auf integrierter GPU.

- Werkstueck-Bounding-Box als Wireframe (orientierung)
- Voxel-Farbe variiert minimal nach Hoehe (heller oben → besseres Tiefen-Gefuehl)
- Maus-Drag dreht, Wheel zoomt (Shift = fein, Ctrl = grob)
- Boden-Gitter (Maschinen-Tisch)

## MCP

```python
material_abtrag_simulieren(toolpaths, werkzeug_id, werkstueck, aufloesung_mm=2.0)
```

Claude kann via Chat sagen: „Simuliere mir wie das Werkstueck nach Operation X aussieht."

## Verwandt

- [Simulation-3D](Simulation-3D) — leichte Linien-Toolpath-Vorschau (kein Material-Abtrag)
- [Werkzeug-Modell](Werkzeug-Modell) — Segmente werden im Stempel beruecksichtigt
