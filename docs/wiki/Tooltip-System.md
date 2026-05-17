# Tooltip-System

> **Status:** ✅ 3 Stufen implementiert (WertTooltip / FachTooltip / CoachMark).
> **Code:** [frontend/src/components/Tooltip.tsx](../../frontend/src/components/Tooltip.tsx) · [fachbegriffe.ts](../../frontend/src/components/fachbegriffe.ts)

Drei Tooltip-Klassen nach Design-Note 7 — alle nicht modal, nicht blinkend, persistent dismissable.

## Stufe 1 · `<WertTooltip>`

Hover an einem Wert zeigt Quelle + Original. Sehr klein, nur Fakten — kein Pfeil-Schickschnack.

```tsx
<WertTooltip inhalt="Material-Preset · Original: 18000 RPM">
  <span>18000</span>
</WertTooltip>
```

## Stufe 2 · `<FachTooltip>`

Inline-`?`-Icon, beim Klick erscheint ein Popover mit Definition + ggf. Formel + ggf. Sicherheits-Hinweis. Schliesst beim Klick ausserhalb. Nutzt das zentrale [fachbegriffe.ts](../../frontend/src/components/fachbegriffe.ts)-Wörterbuch.

```tsx
import { FACHBEGRIFFE } from "../components/fachbegriffe";

<h3>Stepdown <FachTooltip {...FACHBEGRIFFE.stepdown} /></h3>
```

**Vorhandene Fachbegriffe** (`FACHBEGRIFFE.*`): `stepdown`, `stepover`, `vorschub`, `plunge`, `spanlast`, `rampe`, `helix_eintauchen`, `tabs`, `aufmass`, `adaptive_clearing`, `schnittgeschwindigkeit`, `drechseln_drehzahl`.

Neue Begriffe → in `fachbegriffe.ts` ergaenzen, damit die Erklaerung ueberall konsistent ist.

## Stufe 3 · `<CoachMark>`

Erscheint beim ersten Besuch einer View — ein Hinweis-Popover ueber dem markierten Element. Dismissable per `×`-Button, merkt sich „gesehen" in LocalStorage. Optional mit `ablauf_tage` automatisch wieder zeigen.

```tsx
<CoachMark
  id="quickstart_intro"
  text="Vier Vorlagen unten: Klick auf eine, Maße eingeben, fertig."
  ablauf_tage={30}
>
  <h1>Schnellstart</h1>
</CoachMark>
```

LocalStorage-Key: `camwosa.coach.<id>`. `coachMarksZuruecksetzen()` loescht alle (z.B. fuer „Onboarding nochmal zeigen"-Button im Einstellungen-View).

## Design-Prinzipien (Design-Note 7 + 8)

- Nichts blinkt, nichts ist modal, nichts blockiert den User
- Akzentfarbe Orange ist tabu fuer Tooltips — sie wechseln in info-blau / muted-grau
- Touch-Geraete: tap-to-show, tap-anywhere-to-hide
- Keine animierten Tipps, keine erzwungenen Tutorials

## Integration in den existierenden Views

Schon verdrahtet:

| View / Editor | Wo |
|---------------|-----|
| `OverrideOperationForm` | FachTooltips an Vorschub, Plunge, Stepdown, Stepover, Tabs, Aufmass, Eintauchstrategie (via `OverrideField.hilfe`-Prop) |
| `FeedsSpeedsPanel` | Tooltips an Vorschub, Plunge, Stepdown, Stepover, Vc, Spanvolumen |
| `CuttingPresetEditor` | Tooltips in den Tabellen-Spalten-Headern |
| `MaterialEditor` | Tooltip an „Materialeigenschaften" (Schnittgeschwindigkeit) |
| `WerkzeugEditor` | CoachMark an V-Bit-Helfer-Buttons (erklaert wann sie nuetzlich sind) |
| `DrechselnView` | FachTooltip an Helix-Sektion (Werkstueck-Drehzahl) |
| `QuickStartView` | CoachMark beim Intro |

Erweiterungs-Strategie: Neue Stellen bekommen `hilfe="..."`-Prop am vorhandenen Feld bzw. einen `<FachTooltip {...FACHBEGRIFFE.x} />` im Header. Selten ein eigenes Komponenten-Sandkasten oeffnen.

## OverrideField-Erweiterung

`<OverrideField>` hat eine optionale `hilfe`-Prop, die einen Key aus `FACHBEGRIFFE` aufnimmt:

```tsx
<OverrideField
  label="Stepdown" einheit="mm" step={0.1} hilfe="stepdown"
  wert={...} onChange={...} onReset={...}
  quelle={...} effektivAnzeige={...}
/>
```

So bleibt der Aufruf knapp — Tooltip erscheint automatisch neben dem Label.

## Verwandt

- [Design-System](Design-System)
- [First-Run-Wizard](First-Run-Wizard)
- [Per-Feature-Override](Per-Feature-Override)
