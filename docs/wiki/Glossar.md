# Glossar — CAM- und CNC-Begriffe

> **Status:** ✅ Erweitert auf 60+ Begriffe (D36 Subset).

Alle Begriffe die in CAMWOSA vorkommen, knapp erklaert.

## A

**Adaptive Clearing** — Tasche mit trochoidalem Werkzeug-Pfad: konstanter
Werkzeug-Eingriff, sanftere Belastung, schneller. Siehe [Adaptive-Clearing.md](Adaptive-Clearing.md).

**Allowance** — Material das beim Schruppen absichtlich stehen bleibt, damit
Schlichten sauberer schneidet. Wird in mm angegeben. Synonyme: Aufmass, Skin.

**Animation** — Cutter-Symbol bewegt sich entlang Toolpath als Vorschau.
Anders als Simulation, die das fertige Ergebnis zeigt.

**Arbeitsplan** — Druckbare Schritt-fuer-Schritt-Anleitung pro Setup mit
Werkzeug-Wechseln + Foto-Slots. Generiert via [Workflow-Modul](Workflow-Modul.md).

**Aufspannung** — Position + Halterung des Werkstuecks fuer einen
Bearbeitungs-Vorgang. Wechsel = neuer Setup.

## B

**Backplot** — Visuelle Darstellung des Toolpaths.

**Ballnose** — Werkzeug mit Halbkugel-Spitze. Siehe [KUGELFRAESER](Werkzeug-Typen.md#kugelfraeser).

**Border** — Bearbeitungs-Bereich um das Werkstueck herum (typisch
Werkzeug-Radius + Aufmass), wo der Cutter ohne Material lauft.

## C

**Climb** — Gleichlauf-Fraesen: Werkzeug-Rotation und Vorschub in gleicher
Richtung. Sauberere Oberflaeche, hoehere Belastung an Maschine. Gegenteil: Conventional.

**Collet** — Spannfutter der Spindel, in dem der Werkzeug-Schaft steckt.
Pruefen ob Collet mit Werkstueck kollidiert -> `free_length_mm` im Werkzeug.

**Conventional** — Gegenlauf-Fraesen: Werkzeug-Rotation gegen Vorschub.
Sicherer aber rauere Oberflaeche.

**Contour-parallel** — Toolpath folgt der Geometrie-Form (Offset-Bahnen).

**Cusp** — Ueberbleibendes „Wellengipfel"-Material zwischen 2 Ball-Nose-Bahnen.

## D

**Dogbone** — Tasche mit zusaetzlichem Kreis-Ausschnitt an Innenecken, damit
scharfe Zapfen reinpassen. Siehe [Dogbone-Slots](Spezial-Operationen.md).

**Drag-Engraver** — Federbelasteter Diamant der ohne Spindle-Drehung (M5)
unter Eigengewicht eine Linie zieht. Sehr fein.

## E

**Eckenradius** — Verrundeter Uebergang an einer Innen-Ecke. Werkzeug
hinterlaesst immer einen Eckenradius = Werkzeug-Radius. Sonderkonzept
beim Torusfraeser (siehe [Werkzeug-Typen](Werkzeug-Typen.md#torusfraeser)).

**Eilgang** — G0-Bewegung mit max. Vorschub, **ohne Schnitt**. Werkzeug
sollte ueber der Z-Sicherheitshoehe sein.

**Einschneider** — Schaftfraeser mit nur einer Schneide. Sauberer Schnitt
in Holz, hoeherer Vorschub.

## F

**Feedrate** — Vorschub-Geschwindigkeit in mm/min.

**Finishing** — Schlicht-Pass, nimmt nur die Allowance/Skin weg fuer
saubere Oberflaeche.

**Fischschwanz** — Schaftfraeser mit Endschneiden die ueber die Mitte
hinausragen — **plunge-faehig** wie ein Bohrer. Siehe [Werkzeug-Typen](Werkzeug-Typen.md#fischschwanz).

**Flute** — Spirale entlang Werkzeug-Schaft (= die Schneide). „2-Flute" =
2 Schneiden.

**Free Length** — Werkzeug-Laenge vom Collet-Unterkante bis Spitze.
Wichtig fuer Collet-Collision-Check.

## G

**G-Code** — Standard-Sprache fuer CNC-Maschinen. G0=Eilgang, G1=Linear,
G2/G3=Bogen, M3/M5=Spindle an/aus, etc.

**Geometry-Operation** — Operation auf einer 3D-Geometrie (STL/Mesh).
Beispiele: Relief, Schlichten.

**Grayscale-zu-Z** — Konvertierung Bild-Helligkeit -> Material-Tiefe.
Basis fuer Bild-zu-Relief.

## H

**Halter** — Werkzeug-Halter im Spindel-Mount. Kollisions-relevant: Halter
darf nicht ins Werkstueck rammen.

**Heightmap** — 2D-Grid mit Z-Wert pro Position. Output von STL-Analyse +
Input fuer Relief-Toolpath.

**Helix** — Spiralfoermige Bewegung. Beim Helix-Eintauch sinkt das Werkzeug
spiralfoermig ins Material statt geradeaus.

## I

**Indexed Machining** — 4-Achs-Rotary: Werkstueck wird in N Positionen
(z.B. 4 oder 8) rundum bearbeitet, dazwischen automatisch gedreht.

**Inlay** — Einsatz aus Kontrast-Material in eine Tasche.

## K

**Kollisionsanalyse** — Pre-Check ob Werkzeug/Halter mit Werkstueck oder
Spannmittel kollidiert.

## L

**Layer** — Z-Schichten beim Schruppen (= Stepdown).

**Lithophane** — Duenner Relief-Print aus durchscheinendem Material.
Hell = duenn = mehr Licht durch. Siehe [Lithophane.md](Lithophane.md).

## M

**Meander** — Zickzack-Pattern beim Pocketing. Werkzeug schneidet hin
und zurueck. Schnell aber Oberflaeche unterschiedlich auf beiden Seiten.

**Multi-Setup** — Projekt mit mehreren Aufspannungen, jede mit eigenen
Operationen.

## N

**NC** — Numerical Control. CNC = Computerized NC.

**Nesting** — Mehrere Teile platzsparend auf einer Material-Platte
anordnen. Siehe [Nesting.md](Nesting.md).

**Nullpunkt** — Werkstueck-Bezugspunkt (XYZ-Origin). Vom User auf der
Maschine eingestellt.

## O

**Offset** — Versatz einer Kontur um einen bestimmten Wert. Pocketing-
Strategie: Bahnen folgen der Kontur in Offset-Schritten.

**On Curve** — Profile-Strategie wo Werkzeug-Mitte EXAKT auf der Kontur
liegt (Pen-Plotter-Mode).

## P

**Peck** — Bohr-Strategie mit Rueckzug zwischen Z-Schritten, damit Spaene
rauskommen.

**Pencil-Trace** — 3D-Strategie wo nur die Innenecken mit kleinem Werkzeug
nachgefahren werden (was groesseres Werkzeug nicht erreicht hat).

**Plunge** — Werkzeug taucht **gerade nach unten** ins Material. Nur fuer
Bohrer + Fischschwanz-Fraeser sicher. Standard-Schaftfraeser braucht
Helix-Eintauch oder Rampe stattdessen.

**Pocket / Pocketing** — Innen-Material einer geschlossenen Kontur ausnehmen
(= Tasche).

**Profiling** — Werkzeug folgt einer Kontur (Innen/Aussen/Auf Linie).

**Project-Tree** — Hierarchische Darstellung Project > Parts > Operations
mit Sichtbarkeits-Lampen.

## R

**Radial** — 3D-Strategie: Bahnen von Mittelpunkt radial nach aussen.

**Rapid** — = Eilgang (G0).

**Reference Plane** — Bezugsflaeche fuer Wiederaufspannen. Beim
Two-Sided-Machining wichtig.

**Relief** — 3D-Bearbeitung wo Werkzeug der Oberflaeche folgt. Quelle:
Heightmap, Bild, STL.

**Rest-Machining** — Pass der nur das Material entfernt, das vorherige
Operation nicht erreicht hat.

**Roughing** — Schrupp-Pass: schnell viel Material weg, mit Allowance fuer
Finishing.

## S

**Schaftdurchmesser** — Durchmesser des Werkzeug-Schaftes (was im Collet
sitzt). Kann groesser sein als die Schneide (Multi-Diameter).

**Schaftfraeser** — Standard-Endmill mit zylindrischer Schneide + flachem
Boden. Siehe [Werkzeug-Typen](Werkzeug-Typen.md#schaftfraeser).

**Schneidlaenge** — Laenge der Schneide entlang der Werkzeug-Achse.
Max-Eintauchtiefe ohne dass der Schaft schneidet.

**Schruppen** — = Roughing.

**Schlichten** — = Finishing.

**Sicherheits-Hoehe** — Z-Wert ueber Werkstueck-OK, auf den der Cutter
zwischen Operations zurueckgezogen wird. Typ. 5 mm.

**Sicherheitszone** — Bereich wo Toolpath nicht reinfahren darf (z.B.
um Spannmittel).

**Skin** — = Allowance.

**Spannmittel** — Vorrichtung die das Werkstueck am Tisch festhaelt.
Beispiele: Zwinge, Schraubstock, Vakuum.

**Spindle** — Motor mit Werkzeug-Halter. Dreht das Werkzeug.

**Stepdown** — Z-Tiefe pro Schrupp-Pass.

**Stepover** — XY-Abstand zwischen 2 benachbarten Werkzeug-Bahnen.
Als Prozent vom Werkzeug-Durchmesser. Default 40% Pocket, 5-15% Schlichten.

**STL** — Standard-Format fuer 3D-Mesh (Triangle Tessellation).

**Support Tab** — Verbindung zwischen Werkstueck und Block damit Werkstueck
beim letzten Pass nicht abfaellt.

## T

**Tab** — = Support Tab.

**Tasche** — = Pocket.

**Thread Milling** — Gewinde-Fraesen mit Helix-Toolpath.

**Toolpath** — Werkzeug-Pfad (Liste von XYZ-Punkten + Vorschub).

**Torusfraeser** — Schaftfraeser mit verrundetem Eckenradius.
Bull-nose-Cutter. Siehe [Werkzeug-Typen](Werkzeug-Typen.md#torusfraeser).

**Trochoidal** — Kreisbewegung ueberlagert dem Vorschub (siehe Adaptive
Clearing).

**Two-Sided Machining** — Werkstueck wird von beiden Seiten bearbeitet
(Vorder + Rueck). Erfordert Wiederaufspannen mit Reference-Planes.

## V

**Variante** — Auspraegung eines Projekts (z.B. „mit Logo" vs „ohne Logo").

**V-Bit** — Konisch zugespitzes Werkzeug. Standard fuer V-Carving.

**V-Carving** — Schrift-Gravur wo Linienbreite ueber Tiefe variiert.

**Vector-Operation** — Operation die auf 2D-Vektor-Daten (Linien, Bogen)
arbeitet. Beispiele: Profiling, Pocketing.

**Voxel** — 3D-Pixel. Wir nutzen Voxel-Simulation fuer Material-Abtrag.

## W

**Waterline** — 3D-Strategie: Toolpaths auf konstanten Z-Levels (wie
Hoehenlinien). Gut fuer steile Waende.

**Werkzeugwechsel** — Wechsel des Cutters. ATC = Automatic Tool Changer
(haben Hobby-Maschinen meist nicht — manueller Wechsel via Pause).

**Wrap** — 2D-Design auf Zylinder wickeln (Rotary-Mode).

## Z

**Z-Grid** — Diagnose-Tool: Heightmap als 3D-Bargraph visualisiert. Hilft
zu sehen wo Geometrie-Features im Toolpath verloren gehen.

**Zickzack** — = Meander.

---

## Verwandt

- [Werkzeug-Typen](Werkzeug-Typen.md) — alle 12 Cutter-Typen mit Skizzen
- [Operation-Kontur](Operation-Kontur.md), [Operation-Tasche](Operation-Tasche.md), etc.
- [Sicherheits-Checks](Sicherheits-Checks.md)
