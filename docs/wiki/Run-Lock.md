# Run-Lock + Dependency-Graph

> **Status:** ✅ Backend fertig (alpha.3). UI-Verdrahtung folgt in alpha.6+.
> **Code:** [`backend/camwosa/workflow/run_lock.py`](../../backend/camwosa/workflow/run_lock.py)
> **Tests:** [`backend/tests/workflow/test_run_lock.py`](../../backend/tests/workflow/test_run_lock.py) (29/29 grün)
> **API:** `POST /api/workflow/run-lock`

## Markus' Prinzip

> *"Im Zweifel laeuft das Programm nicht."*

Wenn der Projekt-State inkonsistent ist (z.B. ein Werkzeug wurde nach
Toolpath-Berechnung geändert, eine Geometrie wurde gelöscht), darf der
G-Code-Export **nicht** stillschweigend mit stale-Daten erfolgen. Lieber
**blockieren** und den User entscheiden lassen, was er tun will.

## Datenmodell

Jede Operation bekommt ein zusätzliches Feld `status` mit 4 Stufen:

| Status | Bedeutung | Farbe in UI |
|---|---|---|
| `NEU` | Noch nie berechnet | grau |
| `OK` | Toolpath aktuell, alle Quellen gültig | grün |
| `DIRTY` | Quelle hat sich geändert, Recalc nötig | orange |
| `BROKEN` | Quelle fehlt (Werkzeug/Geometrie gelöscht) | rot |

Plus ein `input_hash` (SHA1 über alle Inputs) für Change-Detection.

## Input-Hash

```python
from camwosa.workflow.run_lock import operation_input_hash

hash_a = operation_input_hash(op,
    geometrien_inhalt={"g1": <wkt>},
    werkzeug_inhalt={"t1": <werkzeug-json>},
    material_inhalt={"m1": <material-json>},
)
# Identische Inputs → identischer Hash. Eine Änderung → neuer Hash.
```

Wenn `op.input_hash != aktueller_hash`, ist die Operation **DIRTY** —
auch wenn der Toolpath gespeichert wurde.

## Operation-Status pruefen

```python
from camwosa.workflow.run_lock import pruefe_operation

status, fehlertext = pruefe_operation(
    op,
    geometrie_ids_vorhanden=set(...),
    werkzeug_ids_vorhanden=set(...),
    material_ids_vorhanden=set(...),
)
# status = NEU | OK | DIRTY | BROKEN
# fehlertext = "" wenn OK, sonst "Werkzeug t_alt_fr_3 fehlt" o.ä.
```

## Ganzes Projekt + G-Code-Lock

```python
from camwosa.workflow.run_lock import pruefe_projekt, darf_gcode_generieren

stati = pruefe_projekt(projekt)
# → {"op_1": (OK, ""), "op_2": (BROKEN, "Werkzeug t_x fehlt")}

ok, blocker = darf_gcode_generieren(projekt, variante_id="v1", setup_id="s1")
if not ok:
    print("G-Code-Export blockiert:")
    for b in blocker:
        print(f"  - {b}")
```

## Auto-Invalidation

Wenn eine Geometrie/Werkzeug/Material geändert wird, müssen alle
abhängigen Ops als DIRTY markiert werden:

```python
from camwosa.workflow.run_lock import markiere_abhaengige_dirty

n = markiere_abhaengige_dirty(projekt, werkzeug_ids={"t_fr_3"})
# → Anzahl der jetzt-DIRTY Ops
```

## REST-API

```
POST /api/workflow/run-lock
Body: CWPProjekt JSON

Response:
{
  "ok": false,
  "blocker": ["Operation 'Kontur 1' BROKEN: Werkzeug t_alt fehlt"],
  "status_pro_op": {
    "op_1": "ok",
    "op_2": "broken"
  }
}
```

## UI-Verdrahtung (geplant)

In alpha.6+ soll im Frontend:

- Jede Operation in der Liste den Status-Indikator zeigen (grau/grün/orange/rot)
- Bei BROKEN: rotes Banner über G-Code-Export-Button
- "Toolpath neu berechnen"-Button bei DIRTY
- Auto-Mark-Dirty wenn Geometrie/Werkzeug/Material im Store geändert wird

## Bekannte Einschränkungen

- **Hash-Granularität ist Op-Level** — wenn nur ein Parameter geändert
  wurde, ist die ganze Op DIRTY. Inkrementelle Updates sind out of scope.
- **Manuelle Toolpath-Edits** (z.B. via G-Code-Editor) sind nicht erkennbar —
  der Run-Lock checkt nur Input-Hash, nicht den Toolpath selbst.

## Verwandt

- [Sicherheits-Checks](Sicherheits-Checks) — komplementär (was tut der
  Toolpath, statt was sind die Quellen)
- [Master-Plan](Master-Plan) A48
