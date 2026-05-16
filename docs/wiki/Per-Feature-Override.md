# Per-Feature-Override-System

> **Status:** ✅ Backend + API + Frontend implementiert.
> **Code:** [backend/camwosa/cam/overrides.py](../../backend/camwosa/cam/overrides.py) · [frontend/src/components/OverrideOperationForm.tsx](../../frontend/src/components/OverrideOperationForm.tsx) · **Tests:** [backend/tests/cam/test_overrides.py](../../backend/tests/cam/test_overrides.py)

## Idee

Jede Operation soll **Standardwerte** vom Material-Preset / Projekt-Default uebernehmen, aber pro Feld einzeln ueberschreiben koennen — und auch wieder zuruecksetzen.

Beispiel:

> „Ich moechte diese Tasche mit der Zustellung X, die andere mit Y, und beim
> Vorschub bei dieser Bohrung schlage 200 mm/min drauf. Mach das wieder auf
> Standard zurueck."

## Auswahl-Hierarchie

Beim Aufloesen eines Felds wird in dieser Reihenfolge gesucht:

1. **Override** (operation-spezifisch) — gewinnt immer
2. **Material-Preset** (Werkzeug-Material-Kombi, z.B. Buche + 6mm Schaftfraeser)
3. **Projekt-Default** (gilt fuer alle Operationen im Projekt)
4. **Werkzeug-Wert** (z.B. Spitzenwinkel beim V-Bit)
5. **Fallback** (eingebaute sichere Defaults)

Beim Speichern wird **nur das Override** persistiert — nicht der aufgeloeste
Wert. So bleibt das Projekt portabel: wenn sich der Material-Preset spaeter
aendert, profitieren alle Operationen die das Feld nicht overridden.

## Datenmodell

```python
class KonturOverrides(BaseModel):
    werkzeug_id: str                         # Pflicht
    spindel_rpm: float | None = None         # None = Standard
    vorschub: float | None = None
    seite: KonturSeite | None = None
    tabs_anzahl: int | None = None
    ...
```

Analog: `TaschenOverrides`, `BohrOverrides`, `GravurOverrides`.

## API

### `POST /api/operations/aufloesen`

**Body:**
```json
{
  "typ": "kontur",
  "material_id": "buche_massiv",
  "overrides": {
    "werkzeug_id": "schaft_6mm_2s_hm",
    "vorschub": 1234
  },
  "projekt_defaults": { "sicherheitshoehe": 8.0 }
}
```

**Response:**
```json
{
  "parameter": {
    "werkzeug_id": "schaft_6mm_2s_hm",
    "spindel_rpm": 18000,
    "vorschub": 1234,
    "stepdown": 2.0,
    ...
  },
  "quellen": {
    "spindel_rpm": "material_preset",
    "vorschub": "override",
    "stepdown": "material_preset",
    "sicherheitshoehe": "projekt_default"
  }
}
```

## UI

Jedes Parameter-Feld zeigt:

- **Im Standard-Modus** (Override nicht gesetzt):
  - Anzeige grau mit aufgeloestem Wert
  - Quellen-Label rechts: „Material-Preset", „Projekt-Default", „Werkzeug", „Fallback"
  - Klick auf das Feld macht ein Override auf (Wert wird kopiert, editierbar)
- **Im Override-Modus**:
  - Editierbar (Input/Select/Checkbox)
  - Quellen-Label „uebersteuert" in Orange
  - Reset-Button **↺** rechts: setzt zurueck auf Standard (= null)

Pro Operation gibt es zusaetzlich:
- **„↺ Alle auf Standard"**: loescht alle Overrides der Operation auf einmal
- Anzahl-Anzeige in der Operations-Liste: `n Override`

## Beispiel-Workflow

```
1. Material „Buche massiv" + Werkzeug „6mm Schaftfraeser" gewaehlt
2. Operation „Tasche A" -> alles Standard (aus Buche-Preset)
   -> RPM 18000, Vorschub 2000, Stepdown 2.0
3. Operation „Tasche B" -> Override Stepover_prozent = 25
   -> alles andere Standard, nur Stepover individuell
4. Operation „Tasche C" -> Override Vorschub = 2500, Aufmass = 0.2
   -> RPM/Stepdown weiter aus Preset, Vorschub+Aufmass individuell
5. „↺ Alle auf Standard" auf Tasche C
   -> alle Overrides weg, alles wieder aus Preset
```

## Erweiterung um Projekt-Defaults

`ProjektDefaults` ist im Backend bereits als Dataclass definiert. Das
Frontend sendet sie aktuell noch nicht — kommt mit der „Projekt-
Einstellungen"-UI in der naechsten Iteration. Bis dahin gelten die
Code-Defaults aus `overrides.py`.

## Bekannte Einschraenkungen

- Quellen-Anzeige nur fuer Override-Felder, nicht fuer abgeleitete Felder
  (z.B. `i, j` in Bogen-Bewegungen).
- `ProjektDefaults` noch nicht in der UI editierbar.

## Verwandt

- [Datenmodell](Datenmodell.md) — SchnittParameterPreset im Material
- [Feeds-Speeds](Feeds-Speeds.md) — eigene Auswahl-Hierarchie fuer Berechnung
- [Operation-Kontur](Operation-Kontur.md), [Operation-Tasche](Operation-Tasche.md), [Operation-Bohren](Operation-Bohren.md), [Operation-Gravur](Operation-Gravur.md)
