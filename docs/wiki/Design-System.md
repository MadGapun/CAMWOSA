# Design-System

> **Status:** ✅ Tokens + Theme/Density-Switcher + Vorschau-Modi + Override-Punkte.
> **Code:** [frontend/src/styles/tokens.css](../../frontend/src/styles/tokens.css), [tailwind.config.js](../../frontend/tailwind.config.js), [state/uiPrefs.ts](../../frontend/src/state/uiPrefs.ts)
> **UI-Components:** [components/UIPrefsMenu.tsx](../../frontend/src/components/UIPrefsMenu.tsx), [components/OperationPreview3D.tsx](../../frontend/src/components/OperationPreview3D.tsx), [components/OverrideField.tsx](../../frontend/src/components/OverrideField.tsx), [components/Topbar.tsx](../../frontend/src/components/Topbar.tsx)

Basiert auf der Design Exploration. Werte sind als CSS-Variablen in `tokens.css`, Tailwind mappt seine Klassen auf diese Variablen.

## Farben

### Surfaces (dark / light schaltbar)

| Token | Dark | Light |
|-------|------|-------|
| `--bg-base` | `#0A0A0B` | `#F7F7F5` |
| `--bg-surface` | `#131316` | `#FFFFFF` |
| `--bg-elevated` | `#1A1A1F` | `#FBFBF9` |
| `--bg-overlay` | `#23232A` | `#FFFFFF` |
| `--bg-inset` | `#060607` | `#EFEFEC` |

### Akzent (Orange — die einzige „Aktion + User-Override"-Farbe)

| Token | Wert |
|-------|------|
| `--accent` | `#FF6B00` |
| `--accent-hover` | `#FF8124` |
| `--accent-soft` | `rgba(255, 107, 0, 0.12)` |
| `--accent-line` | `rgba(255, 107, 0, 0.32)` |

### Signal

| Token | Wert | Zweck |
|-------|------|-------|
| `--success` | `#00C26E` | OK, Material-Preset |
| `--warning` | `#FFB800` | Warnung |
| `--danger` | `#FF453A` | Kritisch, Kollision |
| `--info` | `#4A9EFF` | Projekt-Default |

### Override-Quelle-Punkte (6px)

Vor jedem Wert in OverrideField sitzt ein 6px-Punkt — damit ist im peripheren Sehfeld lesbar, wo der Wert herkommt, ohne ins Feld klicken zu muessen.

| Quelle | Token | Farbe |
|--------|-------|-------|
| Material-Preset | `--src-material` | `#00C26E` |
| Projekt-Default | `--src-projekt` | `#4A9EFF` |
| **User-Override** | `--src-override` | `#FF6B00` (mit Akzent-Glow) |
| Werkzeug | `--src-werkzeug` | `#B388FF` |
| Fallback | `--src-fallback` | `#6B6B73` |

CSS-Klasse: `.cw-src-dot.material` / `.projekt` / `.override` / `.werkzeug` / `.fallback`.

## Dichte (Density)

Drei Stufen — wechselbar per UI-Prefs-Menu in der Topbar.

| Stufe | Zeilenhoehe | Body-Schrift | Zweck |
|-------|-------------|--------------|-------|
| `compact` | 26 px | 12 px | 10" Tablet in der Werkstatt |
| `medium` (Default) | 32 px | 13 px | normaler Desktop |
| `comfortable` | 38 px | 14 px | Touch, 34" Curved, Sehkraft |

Per `data-density="…"`-Attribut am `<html>`-Tag — wird in `tokens.css` ausgewertet.

## Theme

`dark` (Default) / `light` per `data-theme`-Attribut. Schalter im UI-Prefs-Menu.

## Live-Vorschau-Modi (Markus' Anforderung)

Pro Operation einstellbar im Preview-Header — Default global im UI-Prefs.

| Modus | Verhalten | Wann |
|-------|-----------|------|
| `aus` | Nur Werkstueck-Box, kein Overlay | Schweres Relief editieren — Render kostet Zeit |
| `vereinfacht` (Default) | Werkstueck + reduzierte Overlay-Geometrie (z.B. Bohrloecher als Punkte ab 80 Stueck, Pfad-Punkte halbiert ab 100) | Standard — schnell genug, sieht Tiefe und Position |
| `komplett` | Volles Overlay mit hoher Detailtiefe | Reviews, Praesentation |

Component: `<OperationPreview3D modus={...}/>` + `<VorschauModusToggle/>` aus [`OperationPreview3D.tsx`](../../frontend/src/components/OperationPreview3D.tsx).

## Tokens-Mapping in Tailwind

In `tailwind.config.js`:

```js
camwosa: {
  bg: "var(--bg-base)",
  surface: "var(--bg-surface)",
  accent: "var(--accent)",
  // ...
}
```

So bleibt Tailwind-Klassen-Syntax (`bg-camwosa-surface`) lesbar, aber Theme + Density wirken sich an einer einzigen Stelle aus.

## Persistierung

UI-Prefs (Theme, Density, Vorschau-Default) per LocalStorage:

| Key | Werte |
|-----|-------|
| `camwosa.theme` | `dark` / `light` |
| `camwosa.density` | `compact` / `medium` / `comfortable` |
| `camwosa.vorschauModus` | `aus` / `vereinfacht` / `komplett` |

Beim App-Start werden die Werte gelesen und auf `<html>` angewendet — keine FOUC.

## Arbeitsbereich maximieren

Drei Chrome-Leisten (Sidebar, Topbar, StatusBar) sind einzeln ein-/ausblendbar. Plus **Fokus-Modus**, der alle drei auf einmal ausschaltet — fuer maximale Flaeche zum Geometrie-Anzeigen.

### Toggles

Schwebende Mini-Toolbar oben rechts (deszent — Opacity 30 %, voll bei Hover):

| Icon | Wirkung |
|------|---------|
| ▣ / ◰ | Fokus-Modus an/aus |
| ▤ | Sidebar an/aus |
| ▔ | Topbar an/aus |
| ▁ | StatusBar an/aus |

### Hotkeys

| Taste | Wirkung |
|-------|---------|
| `F` | Fokus-Modus toggeln (alle Leisten aus) |
| `Esc` | Fokus verlassen |
| `B` | Sidebar toggeln |
| `T` | Topbar toggeln |

Hotkeys greifen NUR wenn kein Eingabefeld den Fokus hat — sicheres Tippen im Editor / in Formularen.

### Persistenz

Sidebar/Topbar/StatusBar-Sichtbarkeit liegt in LocalStorage (`camwosa.sidebarSichtbar` etc.). Der **Fokus-Modus** ist Session-only — nach Reload landest du NICHT in einer scheinbar leeren App.

## Tiefer Zoom

CNC arbeitet auf 0.1 mm und enger. Beide Viewer haben grosszuegige Zoom-Bereiche:

### 2D-Toolpath (Konva)

- Range: 1 % bis 100 000 % (`0.01×` bis `1000×`)
- Mausrad: 10 % pro Schritt
- **Shift + Mausrad**: 2 % pro Schritt (Fein-Zoom auf Detail)
- **Ctrl + Mausrad**: 25 % pro Schritt (grosse Spruenge)
- Buttons: `−` / `1:1` / `+` / `Fit`
- `1:1` setzt auf 1 mm = 1 px

### 3D (OperationPreview3D + Simulation3D)

- Min-Distanz: 0.1× der Werkstueck-Diagonale (sehr nah, fuer kleine Features)
- Max-Distanz: 10× der Diagonale (Uebersicht)
- Mausrad: multiplikativ (10 % pro Step) — gleichmaessiges Zoom-Gefuehl unabhaengig vom Stand
- Shift/Ctrl-Modifier analog zum 2D-Viewer
- Simulation3D nutzt zusaetzlich `OrbitControls` mit Damping fuer fluessigeres Bewegen

## Verwandt

- [Per-Feature-Override](Per-Feature-Override)
- [Frontend](Frontend)
