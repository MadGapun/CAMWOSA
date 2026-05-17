# Werkzeug-Bibliothek

> **Status:** ✅ Komplett (10+2 Werkzeug-Typen, alle mit Validatoren + Tests)
> **Code:** [`backend/camwosa/db/models.py`](../../backend/camwosa/db/models.py) (Werkzeug + WerkzeugTyp)
> **CRUD:** `POST/PUT/DELETE /api/tools/`

Diese Seite ist die Uebersicht ueber das Werkzeug-System in CAMWOSA. Fuer
Details siehe die Sub-Seiten.

## Wo finde ich was?

| Was | Wo |
|---|---|
| **Welche Werkzeug-Typen gibt es?** | [Werkzeug-Typen](Werkzeug-Typen) — 12 Typen mit Skizzen + Anwendung |
| **JSON-Format eines Werkzeugs** | [Werkzeug-Format](Werkzeug-Format) — Felder + Beispiele |
| **Standzeit-Tracking** | [Standzeit-Tracking](Standzeit-Tracking) — Verschleiss pro Werkzeug |
| **Default-Bibliothek** | [`data/tools/standard_werkzeuge.json`](../../data/tools/standard_werkzeuge.json) |
| **CRUD-Endpoints** | [CRUD-API](CRUD-API) — `POST/PUT/DELETE /api/tools/` |
| **Werkzeug im Wizard anlegen** | [First-Run-Wizard](First-Run-Wizard) — Inline-Anlegen seit alpha.4 |
| **Werkzeug-Auswahl in Operation** | [UI-Integration](UI-Integration) — Dropdown + Override pro Op |
| **Collet-Kollision** | [Kollisionsanalyse](Kollisionsanalyse) — Halter-Check via `free_length_mm` |

## Werkzeug-Typen (12)

Siehe [Werkzeug-Typen](Werkzeug-Typen) fuer Skizzen, Anwendung, Pflichtfelder.

- `SCHAFTFRAESER`, `KUGELFRAESER`, `TORUSFRAESER` (Standard-Fräser)
- `V_BIT`, `BALLNOSE_V_BIT` (V-Carving + Hybrid)
- `GRAVIERSTICHEL`, `DIAMANTGRAVIERER`, `DRAG_GRAVIERER` (Gravieren)
- `BOHRER` (Standard-Spiralbohrer)
- `EINSCHNEIDER`, `FISCHSCHWANZ` (Holz-spezifisch)
- `SCHRUPPFRAESER` (Wellen-Profil)

Plus T-Nut-Fraeser, Schwalbenschwanz-Fraeser, Gewindefraeser, Fasenfraeser
als Sub-Varianten von SCHAFTFRAESER (siehe [Spezial-Operationen](Spezial-Operationen)).

## Werkzeug + Operation = Override-Resolution

Jede Operation hat ein `werkzeug_id` plus optionale Overrides pro Parameter.
Standardwerte kommen aus dem CuttingPreset des Materials. Siehe
[CuttingPreset](CuttingPreset) und [Per-Feature-Override](Per-Feature-Override).

## Sharing

Werkzeug-Bundles als JSON koennen exportiert/importiert werden — Default-
Werkzeuge in `data/tools/`, User-Override-Werkzeuge in
`{CAMWOSA_DATA_DIR}/tools/user_*.json`. Siehe [CRUD-API](CRUD-API).

## Verwandt

- [Werkzeug-Typen](Werkzeug-Typen)
- [Werkzeug-Format](Werkzeug-Format)
- [Standzeit-Tracking](Standzeit-Tracking)
- [Feeds-Speeds](Feeds-Speeds)
- [Per-Feature-Override](Per-Feature-Override)
- [Kollisionsanalyse](Kollisionsanalyse)
