# Bearbeitungszeit-Schätzung

> **Status:** ✅ Backend fertig (alpha.9, Cluster K5). UI folgt.
> **Code:** [`backend/camwosa/gcode/zeit_schaetzung.py`](../../backend/camwosa/gcode/zeit_schaetzung.py)
> **Tests:** [`backend/tests/gcode/test_zeit_schaetzung.py`](../../backend/tests/gcode/test_zeit_schaetzung.py) (15/15 grün)
> **API:** `POST /api/operations/zeitschaetzung` · **MCP:** `zeitschaetzung`

## Wozu

„Wie lange dauert das?" ist eine der ersten Anfänger-Fragen — und ein Standard-
Feature jedes Hobby-CAM-Tools (EstlCAM, DeskProto, Carbide Create, LightBurn
zeigen es alle). CAMWOSA hatte bisher nur eine rohe `zeitschaetzung_minuten()`
auf dem Toolpath; dieses Modul macht daraus eine anfänger-taugliche Schicht.

## Was es liefert

- **Schnitt- vs. Eilgang-Zeit getrennt** — zeigt, wo die Zeit hingeht
- **Werkzeugwechsel-Pausen** — bei Job-Aggregation über mehrere Operationen
- **Beschleunigungs-Overhead** — eine reale Hobby-Maschine bremst an jeder Ecke
  ab; die theoretische Zeit (Länge ÷ Vorschub) unterschätzt um ~10–20 %.
  Default-Overhead-Faktor **1.15**.
- **Klartext** — „1 Std 23 Min" / „4 Min 12 Sek"

Bewusst eine *Schätzung*, kein exakter Wert. Anfänger brauchen die Größen-
ordnung, nicht die Sekunde.

## Benutzung (Python)

```python
from camwosa.gcode.zeit_schaetzung import schaetze_toolpath_zeit, schaetze_job_zeit

# Einzelne Operation
z = schaetze_toolpath_zeit(toolpath, eilgang_mm_min=3000)
print(z.klartext)            # "4 Min 12 Sek"
print(z.schnitt_sekunden)    # reine Schnittzeit
print(z.eilgang_sekunden)    # Leerfahrten

# Ganzer Job (mehrere Ops + Werkzeugwechsel)
z = schaetze_job_zeit(
    [tp_schruppen, tp_schlichten, tp_bohren],
    eilgang_mm_min=3000,
    werkzeugwechsel_sekunden=45,   # manueller Wechsel kostet Zeit
    overhead_faktor=1.15,
)
print(z.klartext)
```

Ein Werkzeugwechsel wird gezählt, wenn sich die `werkzeug_id` zwischen
aufeinanderfolgenden Toolpaths ändert.

## REST-API

```
POST /api/operations/zeitschaetzung
{
  "toolpaths": [ ...serialisierte Toolpaths... ],
  "maschine_id": "..."  ODER  "eilgang_mm_min": 3000,
  "overhead_faktor": 1.15,
  "werkzeugwechsel_sekunden": 45
}
→ { schnitt_sekunden, eilgang_sekunden, pausen_sekunden,
    gesamt_sekunden, gesamt_minuten, klartext }
```

Mit `maschine_id` wird der Eilgang der Maschine genutzt; alternativ direkt
`eilgang_mm_min`. MCP: `zeitschaetzung(toolpaths, maschine_id=...)`.

## Bekannte Einschränkungen

- **Bögen** (G2/G3) werden über die Sehne genähert (leicht unterschätzt) —
  vernachlässigbar, da nach Arc-Fitting die meisten Bahnen ohnehin linear sind.
- **Dwell/Pausen** im Toolpath (z.B. Drag-Engraving-Ecken) sind noch nicht
  einberechnet — Erweiterung möglich.
- Der Overhead-Faktor ist eine Pauschale; eine maschinen-spezifische
  Beschleunigungs-Modellierung wäre genauer.

## Verwandt

- [Cluster K Anfänger-Erlebnis](Master-Plan.md) (K5)
- [Sicherheits-Checks](Sicherheits-Checks.md) · [Arbeitsplan](Arbeitsplan.md)
