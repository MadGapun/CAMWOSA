# UI-Integration: was steckt wo zusammen

> **Status:** ✅ Editoren in den Views eingebettet, Live-Preview verdrahtet.

Komponenten-Uebersicht: wer wird wo gerendert und wie kommunizieren sie.

## OperationenView

```
+-----------------------------------------+
| OperationenView                         |
|  ┌──────────┐  ┌──────────────────────┐ |
|  │ Liste    │  │ Header (Name, WZ, ↺) │ |
|  │ (kontur, │  ├──────────────────────┤ |
|  │  tasche, │  │ OverrideOperationForm│ |
|  │  ...)    │  │  (Parameter)         │ |
|  │          │  ├──────────────────────┤ |
|  │          │  │ FeedsSpeedsPanel     │ |
|  │          │  ├──────────────────────┤ |
|  │          │  │ Live-Preview-Panel   │ |
|  │          │  │  + VorschauModus-    │ |
|  │          │  │     Toggle           │ |
|  │          │  │  + OperationPreview3D│ |
|  │          │  ├──────────────────────┤ |
|  │          │  │ Sicherheits-Bericht  │ |
|  │          │  │ ToolpathStats        │ |
|  └──────────┘  └──────────────────────┘ |
+-----------------------------------------+
```

**Live-Preview reagiert auf**:
- `max_tiefe` aus den Operation-Parametern → Tiefe der Tasche im 3D
- Aktuelle Geometrie (erste passende) → Form/Position
- Vorschau-Modus (`aus` / `vereinfacht` / `komplett`) → Render-Aufwand

Kein Toolpath-Rerender noetig. Wer den echten Toolpath sehen will, klickt
„Toolpath berechnen" und wechselt zu Preview oder Simulation3D.

## WorkflowView

```
+-----------------------------------------+
| WorkflowView                            |
|  Setup 1                                |
|   ├── Header (Name, Modus, Werkzeug)   |
|   ├── Spannmittel + Notizen + FotoSlot |
|   └── ▸ Schritt-Liste                  |
|          ├── SchrittListeEditor        |
|          │   - + Operation             |
|          │   - + Werkzeugwechsel       |
|          │     (mit Strategie-Dropdown)|
|          │   - + ManualNC / Pause / .. |
|          │   - drag / aktivieren /     |
|          │     loeschen                |
|          │   - „aktives WZ danach"     |
|          │     pro Zeile               |
|          └── Hinweis bei leerer Liste  |
|              („Schruppen + Schlichten")|
|  Setup 2                                |
|   ...                                   |
+-----------------------------------------+
```

Die SchrittListe ist initial geschlossen — wer den klassischen Multi-WZ-
Workflow (Schruppen + Werkzeugwechsel + Schlichten) bauen will, klappt
sie auf. Default-Verhalten (leere Liste) leitet die Schritte aus
`pause_vor + operationen` ab — keine Migration noetig.

## AnnotationenEditor (vorbereitet)

Steht als eigenstaendige Komponente bereit (siehe [Geometrie-Annotationen](Geometrie-Annotationen)),
muss noch in den ZeichnenView eingebunden werden. Der Editor allein liefert:

- Hinzufuegen von Anschlagbohrungen / Refpunkten / Kommentaren / Ausschnitten
- Position editierbar als XYZ-Felder
- Optional `onPosWaehlen`-Callback: ruft der Caller den 2D-Viewer auf, dort kann
  der User per Klick die Position setzen — die Koordinaten werden dann via
  Callback zurueckgegeben

## OperationPreview3D — drei Modi pro Operation

Header zeigt einen Toggle (`Aus` / `Vereinfacht` / `Komplett`). Bei vielen
Punkten / Bohrloechern blendet der Hint „viele Punkte — Vereinfacht empfohlen"
ein. Der Modus pro Operation ueberschreibt den Global-Default aus UI-Prefs.

## Verwandt

- [Design-System](Design-System)
- [ArbeitsSchritt](ArbeitsSchritt)
- [Multi-Werkzeug-Setup](Multi-Werkzeug-Setup)
- [QuickCAM](QuickCAM)
- [Geometrie-Annotationen](Geometrie-Annotationen)
