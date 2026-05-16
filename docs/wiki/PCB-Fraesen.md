# PCB-Isolationsfraesen

> **Status:** ✅ Implementiert (Phase E8).
> **Code:** [backend/camwosa/cam/pcb.py](../../backend/camwosa/cam/pcb.py) · **Tests:** [backend/tests/cam/test_pcb.py](../../backend/tests/cam/test_pcb.py)

Werkzeug (Gravurstichel oder V-Bit) fraest Isolationsspuren zwischen Leiterbahnen einer Platine.

## Vorgehen

1. **Input:** geschlossene Polygone der Leiterbahnen / Pads (typisch aus Gerber→DXF-Konvertierung).
2. Pro Leiterbahn wird ein Offset-Pfad mit halbem Isolations-Abstand erzeugt.
3. Werkzeug folgt mit konstanter Tiefe (typisch 0.1-0.2 mm).
4. Optional: mehrere konzentrische Spuren fuer breitere Isolation.

## Verwendung

```python
from camwosa.cam.pcb import erzeuge_pcb_isolation_toolpath, PCBParameter
from shapely.geometry import Polygon

leiterbahnen = [Polygon([(0,0),(10,0),(10,5),(0,5)]), ...]

p = PCBParameter(
    werkzeug_id="gravierstichel_03",
    spindel_rpm=20000,
    vorschub=300,
    eintauch_vorschub=100,
    sicherheitshoehe=1.5,
    isolations_tiefe=0.15,
    isolations_abstand=0.3,
    anzahl_spuren=2,
)
tp = erzeuge_pcb_isolation_toolpath(leiterbahnen, werkzeug, p)
```

## Tipps

- **Spitzenwinkel:** 30° fuer feine Spuren, 60° fuer robustere Bahnen.
- **Tiefe:** Kupfer auf FR4 ist typisch 35 µm — Tiefe 0.1-0.15 mm reicht.
- **Vorschub** sehr niedrig (200-400 mm/min), Spindel sehr hoch.
- **Mehrere Spuren** bei dichten Layouts, damit Restkupfer sicher weg ist.
- **Z-Probe** vor dem Fraesen — selbst kleine Hoehenvariationen ruinieren das Ergebnis.

## Bekannte Einschraenkungen

- Kein Auto-Routing der Spuren-Reihenfolge (Optimierung Verfahrweg).
- Keine Auto-Bohrungen fuer Vias — separat als Bohren-Operation.
- Kein Gerber-Direkt-Import — Konvertierung zu DXF/SVG erforderlich (z.B. via FlatCAM).

## Verwandt

- [Operation-Gravur](Operation-Gravur)
- [CAD-Import](CAD-Import)
