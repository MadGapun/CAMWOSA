# Spindel-System

> **Status:** ✅ Backend + API + Frontend implementiert.
> **Code:** [backend/camwosa/db/models.py](../../backend/camwosa/db/models.py) (Spindel-Klasse) · **Tests:** [backend/tests/db/test_spindel.py](../../backend/tests/db/test_spindel.py)

CAMWOSA behandelt Spindeln als **eigene Entitaeten**, nicht nur als Attribute der Maschine. So koennen mehrere Spindeln einer Maschine zugeordnet sein (z.B. OEM-Router + Makita-Upgrade), und die aktive Spindel wird pro Projekt gewaehlt.

## Wozu eigene Spindeln?

- **Spindel-Upgrades sind die Regel**, nicht die Ausnahme — Genmitsu-User wechseln haeufig vom OEM-Router zur Makita RT0700 oder zu einer PWM-/Wasser-Spindel.
- **Sicherheits-Checks brauchen die richtige RPM-Range**: eine PWM-Spindel hat andere Limits als eine manuelle.
- **Feeds & Speeds** muessen gegen die tatsaechliche Spindel rechnen, nicht gegen die Maschinen-Spec.
- **Postprozessor**-Verhalten haengt ab vom Spindel-Typ (M3/M5 mit oder ohne S, PWM-Promille, Rampe).
- **Community-Sharing**: andere User mit derselben Maschine, aber anderer Spindel, koennen mein Profil ohne Anpassung uebernehmen.

## Datenmodell

```python
class Spindel:
    id: str
    name: str
    hersteller: str
    modell: str
    typ: SpindelTyp                # manuell | PWM | analog
    rpm_min: float
    rpm_max: float
    leistung_watt: float | None
    drehmoment_ncm: float | None
    gewicht_g: float | None
    schaft_durchmesser_mm: float | None
    kuehlung: str                  # luft | wasser | sonstige
    pwm_min_promille: float | None # PWM-Range
    pwm_max_promille: float | None
    rampen_zeit_s: float | None    # Hochlauf-Zeit
    herkunft: SpindelHerkunft      # oem | upgrade | eigenbau
    notizen: str
```

## Maschine + Spindeln

```python
class Maschine:
    spindel_ids: list[str]         # IDs verfuegbarer Spindeln
    aktive_spindel_id: str | None  # welche ist montiert
    # Inline-Felder bleiben als Fallback fuer Schema-v1-Profile
    spindel_typ: SpindelTyp
    spindel_rpm_min: float
    spindel_rpm_max: float

    def aktive_spindel(self, spindel_index) -> Spindel | None: ...
    def effektive_rpm_range(self, spindel_index) -> tuple[float, float]: ...
```

**Auswahl-Hierarchie zur Laufzeit:**
1. Vom User pro Projekt gewaehlte Spindel (UI: ProjektView)
2. `aktive_spindel_id` der Maschine (Default)
3. Inline-Felder `spindel_rpm_*` (Schema-v1-Fallback)

## Mitgelieferte Spindeln (`data/spindles/standard.json`)

| ID | Name | Typ | RPM | Leistung | Herkunft |
|----|------|-----|-----|----------|----------|
| `makita_rt0700` | Makita RT0700C | manuell | 10000–30000 | 710 W | upgrade |
| `genmitsu_router_710w` | Genmitsu Router 710W | manuell | 10000–30000 | 710 W | OEM |
| `generic_pwm_24k` | Generic 24K PWM | PWM | 6000–24000 | 500 W | upgrade |
| `generic_pwm_30k_800w` | Generic 30K PWM 800W | PWM | 8000–30000 | 800 W | upgrade |
| `watercool_2_2kw_24k` | 2.2 kW Wasser ER20 | analog | 6000–24000 | 2200 W | upgrade |

## API

| Endpoint | Zweck |
|----------|-------|
| `GET /api/spindles/` | Liste aller Spindeln |
| `GET /api/spindles/<id>` | Details einer Spindel |
| `POST /api/spindles/validate` | Profil-Validierung |
| `GET /api/machines/<id>/export` | Maschinen-Bundle JSON (Maschine + alle Spindeln) |
| `POST /api/machines/import` | Bundle validieren (Konsistenz Maschine ↔ Spindeln) |

Maschinen-API ist **Spindel-aware** — `GET /api/machines/` liefert pro Maschine:
- `_aktive_spindel` (vollstaendiges Spindel-Objekt)
- `_verfuegbare_spindeln` (Liste)
- `_effektive_rpm_min` / `_effektive_rpm_max`

## Sicherheits-Checks gegen Spindel

`POST /api/safety/check` akzeptiert optional `spindel_id` — sonst wird die aktive Spindel der Maschine genommen. Geprueft werden RPM-Range, Wasserkuehlung-Hinweis, etc.

```python
bericht = pruefe_toolpath(
    toolpath, maschine, werkzeug,
    spindel=spindel,    # gegen Spindel-RPM-Range pruefen
)
```

## Feeds & Speeds gegen Spindel

```python
berechne_feeds_speeds(
    maschine, werkzeug, material,
    rpm_wunsch=18000,
    spindel=spindel,    # Limits aus Spindel-Range
)
```

## UI

### MaschinenView

- Pro Maschine Liste aller zugeordneten Spindeln
- Aktive Spindel hervorgehoben
- **📦 Bundle**-Button: exportiert Maschine + alle Spindeln als JSON-Datei

### ProjektView

- Drei-Spalten-Auswahl: Maschine · Spindel · Material
- Spindel-Dropdown listet alle der aktiven Maschine zugeordneten Spindeln
- „↺ auf Maschinen-Default zuruecksetzen" loescht den Override

### Topbar

- Zeigt aktive Maschine **und** aktive Spindel mit RPM-Range

## Community-Sharing

Maschinen-Profile werden als **Bundle** geteilt — die JSON-Datei enthaelt die Maschine + alle referenzierten Spindeln in einem Stueck:

```json
{
  "schema_version": 1,
  "typ": "camwosa.machine_bundle",
  "maschine": { ...Maschine... },
  "spindeln": [ {...Spindel1...}, {...Spindel2...} ]
}
```

Workflow:
1. Maschinen-Owner exportiert via **📦 Bundle**-Button → JSON-Datei
2. Teilt sie (z.B. via Issue, Forum, GitHub-PR)
3. Anderer User waehlt **„Bundle importieren"** in MaschinenView → Validierung
4. Wenn OK: Datei in `data/machines/community/` (und Spindeln in `data/spindles/community/`) ablegen → beim naechsten App-Start automatisch geladen

## Anlegen einer eigenen Spindel

JSON-Datei in `data/spindles/community/` ablegen (oder direkt in `data/spindles/`):

```json
[
  {
    "id": "meine_spindel",
    "name": "Meine Spindel",
    "hersteller": "Hersteller",
    "modell": "Modell",
    "typ": "PWM",
    "rpm_min": 8000,
    "rpm_max": 24000,
    "leistung_watt": 1500,
    "kuehlung": "luft",
    "pwm_min_promille": 250,
    "pwm_max_promille": 1000,
    "rampen_zeit_s": 3.0,
    "herkunft": "upgrade",
    "notizen": "..."
  }
]
```

## Spindel-Editor (UI)

Seit alpha.14 sind **alle** Spindel-Werte in der UI editierbar (vorher nur per
JSON). In **Maschinen** → Abschnitt **Spindel-Bibliothek**:

- **+ Neue Spindel** / ✏ bearbeiten / 🗑 löschen — `editor/SpindelEditor.tsx`.
- Felder: Name, Hersteller/Modell, **Steuerungs-Typ** (manuell/PWM/analog),
  Herkunft, **RPM min/max**, Leistung, Drehmoment, **Spannzangen-Ø**, Kühlung,
  **Hochlauf-Dwell** (VFD-Accel → `G4 P` vor Erstschnitt), PWM-Kennlinie, Notizen.
- Pro Maschine: **„aktiv"** setzt die aktive Spindel für das aktuelle Projekt
  (Session-Override; das Maschinenprofil bleibt unverändert).

Default-Spindeln aus der Sammel-Datei (`data/spindles/standard.json`) lassen sich
durch eine gleichnamige **User-Override**-Datei übersteuern (Backend-CRUD schreibt
solche Einzeldateien).

> **Hochlauf-Dwell vs. Warmlauf:** `rampen_zeit_s` ist der kurze Dwell, bis die
> Spindel nach `M3` auf Drehzahl ist (VFD-Accel, z.B. 3 s) — er steht vor *jedem*
> Erstschnitt. Der manuelle **Warmlauf** (z.B. 10 s Routine, um die Lager warm zu
> fahren) ist davon getrennt; ein automatischer Programmstart-Warmlauf ist als
> Folge-Option vorgemerkt.

## Verwandt

- [Datenmodell](Datenmodell)
- [Maschinenprofil-Format](Maschinenprofil-Format)
- [Maschine-ProVerXL-4030-V2](Maschine-ProVerXL-4030-V2)
- [Sicherheits-Checks](Sicherheits-Checks)
- [Feeds-Speeds](Feeds-Speeds)
- [Postprozessor-GRBL](Postprozessor-GRBL)
