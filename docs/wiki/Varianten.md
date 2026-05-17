# Varianten

> **Status:** ✅ Backend + Frontend-Switcher.
> **Code:** [backend/camwosa/project/schema.py](../../backend/camwosa/project/schema.py) (Datenmodell) · [frontend/src/state/varianteStore.ts](../../frontend/src/state/varianteStore.ts) (State) · [frontend/src/components/VarianteSwitcher.tsx](../../frontend/src/components/VarianteSwitcher.tsx) (UI)
> **Master-Plan-Position:** [A19](Master-Plan.md)

Ein Projekt kann **mehrere Varianten** halten. Jede Variante teilt die
Geometrien (Zeichnung, importierte DXF/SVG/STL) mit den anderen, hat aber
ihre **eigenen Operationen, Setups, ihr eigenes Rohmaterial und Notizen**.

## Warum Varianten

Typische Anwendungsfaelle:

- **"Schruppen" vs "Schlichten" als getrennte Strategien**, damit man sie
  einzeln anklicken / generieren kann ohne den anderen zu verlieren.
- **"Holz" vs "MDF" vs "Sperrholz"** — gleiches Werkstueck, aber andere
  Feeds & Speeds und ggf. andere Operations-Reihenfolge.
- **"Prototyp" vs "Serienteil"** — Prototyp mit Sicherheits-Tabs ueberall,
  Serienteil mit optimierten Tabs an wenigen Stellen.
- **"3-Achs" vs "Rotary"** — gleiche Geometrie als Skizze, einmal flach
  ausgefraest, einmal als Wrap auf eine Saeule gewickelt.
- **A/B-Tests von Werkzeug-Strategien** — "klassisch" vs "adaptive
  clearing" — Daten parallel halten und vergleichen.

## Datenmodell (Backend)

```python
class Variante(BaseModel):
    id: str
    name: str
    rohmaterial: Rohmaterial
    setups: list[Setup] = []
    annotationen: list[GeometrieAnnotation] = []  # Werkstueck-Annotationen
    notizen: str = ""

class CWPProjekt(BaseModel):
    ...
    geometrien: list[GeometrieSnapshot] = []  # GETEILT zwischen Varianten
    varianten: list[Variante] = []
    metadaten: ProjektMetadaten  # enthaelt aktive_variante: str
```

Wichtig: `geometrien` lebt auf **Projekt-Ebene**, nicht in der Variante.
Wer pro Variante andere Geometrien braucht, legt ein neues Projekt an.

## Snapshot-Logik (Frontend)

Der Frontend-Store haelt die "Working-Stores" flach:

- `useAppStore.operationen`
- `useWorkflowStore.setups`
- `useRohmaterialStore.rohmaterial`

Beim **Wechsel der aktiven Variante** macht `useVarianteStore.wechseln(id)`:

1. **Snapshot der aktuellen Working-Stores** in die bisherige aktive
   Variante zurueckschreiben.
2. **Snapshot der neuen Variante** in die Working-Stores laden.

So bleibt die Bedienung im Operations-Editor, im SchrittListe-Editor, im
RohmaterialEditor exakt dieselbe wie ohne Varianten. Varianten sind reine
Snapshot-Aufbewahrung — keine View muss umgebaut werden.

## Bedienung (UI)

In der Topbar steht der `VarianteSwitcher`:

```
V: [Default ▼]  [⚙]
```

- Das Dropdown wechselt die aktive Variante.
- Das Zahnrad oeffnet das Verwaltungs-Modal mit:
  - Tabelle aller Varianten (aktiv-Radio, Name editierbar, Operations-/Setup-Zaehler, Notizen)
  - Eingabe + Button "+ Leere Variante"
  - Button "⧉ Aktive duplizieren" — uebernimmt Rohmaterial + Operationen + Setups (mit neuen IDs)
  - "Loeschen"-Button pro Variante (disabled wenn nur eine Variante existiert)

Beim Duplizieren werden **neue IDs** fuer Operationen + Setups erzeugt,
damit Verweise (z.B. aktive Operation) keine Konflikte ergeben.

## Persistenz

Beim Speichern als `.cwp` exportiert `exportiereVarianten()` die komplette
Variante-Liste. Der Backend-Side `CWPProjekt.varianten` nimmt diese auf,
plus `metadaten.aktive_variante` als String-ID.

Beim Laden ruft die Projekt-Lade-Logik (kommt mit
[D4 Projekt-Verwaltung Frontend](UI-Projekt.md)) `useVarianteStore.init()`
auf, das die Liste setzt und die aktive Variante in die Working-Stores
laedt.

## Bekannte Einschraenkungen

- **Geometrien werden geteilt** — wer pro Variante eine andere Form
  braucht, soll ein neues Projekt anlegen. (Bewusste Design-Entscheidung,
  vermeidet doppelte Geometrie-Editoren.)
- **Annotationen pro Geometrie** (`GeometrieSnapshot.annotationen`) sind
  ebenfalls geteilt. Variante-eigene Annotationen sind nur die
  Werkstueck-Annotationen (`Variante.annotationen`) — wird in einem
  spaeteren Schritt aus dem Frontend angesprochen.
- **Aktive Variante wird nicht persistent gespeichert** zwischen App-Starts —
  der Snapshot im Store ist Working-Memory. Nach Reload startet die App
  mit `default`-Variante leer.

## Verwandt

- [Projekt-Format](Projekt-Format.md) — `.cwp`-ZIP-Container
- [ArbeitsSchritt](ArbeitsSchritt.md) — Setup-Schritte je Variante
- [Workflow-Modul](Workflow-Modul.md) — Multi-Setup-Workflow
