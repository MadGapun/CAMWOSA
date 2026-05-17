# First-Run-Wizard

> **Status:** ✅ 4-Schritt-Onboarding nach Design-Note 6.
> **Code:** [frontend/src/components/FirstRunWizard.tsx](../../frontend/src/components/FirstRunWizard.tsx)

Das Onboarding fuehrt **nicht durch alle Features** (wie typische Pro-CAM-Tools), sondern fokussiert auf die 4 Setup-Entscheidungen, die der User einmal trifft und dann lange Zeit nicht aendert.

## Die 4 Schritte

1. **Maschine** — welche CNC. Beeinflusst Arbeitsraum, Controller, Default-Postprozessor
2. **Spindel** — welche der verfuegbaren Spindeln der Maschine gerade montiert ist. Wichtig fuer RPM-Range
3. **Erstes Werkzeug** — was eingespannt ist. Spaeter beliebig viele dazu
4. **Material** — was bearbeitet wird. Bestimmt Default-Feeds-&-Speeds

Jeder Schritt zeigt nur die fuer den Vorgaenger relevanten Optionen (z.B. nur Spindeln der gewaehlten Maschine).

## Verhalten

- Erscheint **einmalig** beim ersten App-Start (Detektion ueber `localStorage`-Key `camwosa.firstRunDone`)
- Lässt sich **„Spaeter"** klicken — dann ist die Auswahl uebersprungen, aber der Wizard kommt nicht von alleine wieder
- Lässt sich **erneut zeigen** ueber `firstRunZuruecksetzen()` (z.B. im EinstellungenView ein Button „Onboarding nochmal zeigen")
- Modal-Overlay mit Backdrop, Tastatur-`Esc` fuer Abbruch

## Design-Prinzipien (aus Design-Note 6 + 8)

- **Kein Tutorial-Geist** — keine Coach-Marks, keine animierten Tipps, kein blockendes „Beachte hier!"
- **Auswahl statt Lesen** — jede Karte zeigt nur Name + 1 Zeile Details
- Footer zeigt **Progress-Dots** (4 schmale Balken) statt einer „X von 4"-Schrift
- Nur die Akzentfarbe Orange ist „Aktion + Auswahl" — sonst keine bunten Highlights

## Verwandt

- [Design-System](Design-System)
