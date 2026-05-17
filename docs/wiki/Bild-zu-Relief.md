# Bild-zu-Relief

> **Status:** ✅ **Phase A + B + C + D Backend fertig** (Backend + API + MCP + Frontend + Wrap-Kombination + Bearbeitungs-Tools + Tests). Phase D Frontend-Filterpanel und Phase E (AI-Tiefenschaetzung) sind als Master-Plan-Positionen vorgemerkt.
> **Code:** [stl/bild_heightmap.py](../../backend/camwosa/stl/bild_heightmap.py) (Bild → Heightmap, Phase A) + [stl/heightmap_bearbeitung.py](../../backend/camwosa/stl/heightmap_bearbeitung.py) (Bearbeitungs-Tools, Phase D) + [cam/relief.py](../../backend/camwosa/cam/relief.py) (Heightmap → Flach-Toolpath) + [cam/wrap.py](../../backend/camwosa/cam/wrap.py) (Wrap-Relief, Phase C) + [stl/heightmap.py](../../backend/camwosa/stl/heightmap.py) (Datenmodell)
> **API:** `POST /api/heightmap/aus-bild` · `aus-bild/statistik` · `wrap-relief` · `wrap-relief/pruefen` · `bearbeitung/gamma` · `bearbeitung/histogramm-stretch` · `bearbeitung/zero-plane` · `bearbeitung/edge-boost` · `bearbeitung/selective-smoothing` · `bearbeitung/detail-slider`
> **MCP:** `heightmap_aus_bild_statistik`
> **Tests:** [test_bild_heightmap.py](../../backend/tests/stl/test_bild_heightmap.py) (10) · [test_heightmap_bearbeitung.py](../../backend/tests/stl/test_heightmap_bearbeitung.py) (22) · [test_heightmap_api.py](../../backend/tests/api/test_heightmap_api.py) (20) · [test_wrap.py](../../backend/tests/cam/test_wrap.py) (12 Wrap-Relief + 17 Wrap-Standard)

## Worum es geht

Markus moechte: aus einem normalen Bild (Foto, Logo, Tiefenbild) automatisch
ein 3D-Relief erzeugen, das dann optional auf einen Zylinder gewickelt
werden kann (Drechselsaeule mit „Photo-Carving" o.ae.). Industrie-Tools die
das koennen:

- **Carveco** (ex-ArtCAM) — Marktfuehrer, mit AI-Image-to-Relief seit 2024
- **Vectric Aspire / PhotoVCarve**
- **PixelCNC** (Deftware)
- **VistaSculpt** — AI-basiert
- **Sculptok** — AI Bild → Heightmap
- **Relief Maker**

Alle bauen im Kern auf zwei Algorithmen: **Bild → Heightmap** und
**Heightmap → Toolpath**. Wrap kommt obendrauf als reine
Koordinaten-Transformation.

## Drei Verarbeitungsstufen

Wir bauen das schrittweise ab — von einfach nach komplex. Jede Stufe ist
fuer sich nuetzlich.

### Stufe 1: Grayscale-Heightmap (einfach, klassisch) ✅ **fertig**

**Implementation steht** in [stl/bild_heightmap.py](../../backend/camwosa/stl/bild_heightmap.py).

User laedt ein Bild (PNG/JPG/...), das System konvertiert es nach Grayscale
und erzeugt eine `Heightmap`-Datenstruktur kompatibel zum existing
`cam.relief.erzeuge_relief_toolpath` — d.h. die komplette Toolpath-Pipeline
funktioniert direkt.

**Parameter** (`BildHeightmapParameter`):
- `max_tiefe_mm` (Default 3.0) — Tiefen-Spanne zwischen weiss und schwarz
- `pixel_pro_mm` (Default 5.0) — Aufloesung (5 = 0.2mm Pixel)
- `invertieren: bool` (Default False) — False: weiss=hoch · True: dunkel=hoch
- `glaetten_radius: int` (Default 0) — Box-Blur Radius in Pixel (1-5 fuer Glaettung)
- `zero_plane_schwelle` (Default 0) — Helligkeiten ueber dieser Schwelle (0..1) werden auf Z=0 gesetzt (Sockel-Effekt fuer Motiv-Hintergrund-Trennung)
- `max_dimension_px` (optional) — herunter-skalieren um riesige Toolpaths zu vermeiden

**API**:
```bash
curl -F "datei=@logo.png" \
     -F "max_tiefe_mm=2" \
     -F "pixel_pro_mm=4" \
     -F "invertieren=false" \
     -F "glaetten_radius=2" \
     http://localhost:8765/api/heightmap/aus-bild
```

Antwortet mit:
- `aufloesung_mm`, `x_min_mm`, `y_min_mm`, `z_max_mm`
- `shape: [nx, ny]`
- `z_values_base64` — float32-Array komprimiert base64 (kompakter als JSON-Listen)
- `statistik` — Diagnose (Z-Min/Max/Mittel, Anzahl-Pixel, Breite/Hoehe in mm)

Plus `/api/heightmap/aus-bild/statistik` fuer schnelle Live-Vorschau ohne Z-Array.

**MCP**: `heightmap_aus_bild_statistik(bild_base64, max_tiefe_mm, pixel_pro_mm)` — Claude kann via Bild-Inline-Anhang Statistiken anfordern.

**Limitierungen**:
- Helligkeit ist subjektiv (manche Fotos liefern flache Reliefs)
- Anti-Aliasing-Pixel koennen sichtbare Streifen erzeugen — Glaettung hilft
- Bildrauschen wird direkt mitgefraest
- Glaetten ist als Box-Blur implementiert (scipy-frei). Bei sehr grossen Bildern (>2 MP)
  + grossem Radius wird der Loop spuerbar — `max_dimension_px` setzen.

### Stufe 2: Heightmap-Bild + Vorverarbeitung ✅ **Backend fertig (Phase D)**

**Implementation steht** in [`stl/heightmap_bearbeitung.py`](../../backend/camwosa/stl/heightmap_bearbeitung.py)
als pure Funktionen die jeweils eine neue Heightmap zurueckliefern (immutable
Style — die alte bleibt unveraendert, kann fuer Undo benutzt werden):

| Funktion | Was sie tut |
|----------|-------------|
| `gamma_korrektur(hm, gamma)` | Helligkeits-Kurve. ``gamma>1`` macht Mid-Tones tiefer, ``<1`` flacher. |
| `histogramm_stretch(hm, low_perz, high_perz)` | Streckt Kontrast zwischen 2 Perzentilen. |
| `zero_plane(hm, schwelle)` | Pixel mit Helligkeit > Schwelle → Z=0 (Hintergrund-Sockel). |
| `edge_boost(hm, faktor)` | Sobel-Kantenverstaerkung — Konturen werden tiefer. |
| `selective_smoothing(hm, radius, bereich, schwelle)` | Box-Blur **nur** in hellen/dunklen/allen Bereichen. |
| `detail_slider(hm, detail)` | Carveco-style Slider von -1 (weich) bis +1 (scharf). |

Alle Filter sind **scipy-frei** (manueller Sobel + Box-Blur), also keine
zusaetzlichen Dependencies. Die Funktionen sind chain-bar — typische
Pipeline:

```python
from camwosa.stl.heightmap_bearbeitung import (
    gamma_korrektur, zero_plane, edge_boost,
)

hm = heightmap_aus_bild(bild_bytes)
hm = gamma_korrektur(hm, gamma=1.4)     # Mid-Tones dunkler
hm = zero_plane(hm, schwelle=0.85)      # Heller Hintergrund auf Z=0
hm = edge_boost(hm, faktor=0.6)         # Konturen schaerfer
# → fertig fuer cam.relief.erzeuge_relief_toolpath
```

**API**: pro Filter ein Endpoint unter `/api/heightmap/bearbeitung/…`. Jeder
Endpoint nimmt eine Heightmap entgegen (gleiches Payload-Format wie
`/api/heightmap/aus-bild` liefert) und gibt eine neue Heightmap zurueck —
ideal fuer ein Live-Preview mit Filter-Stack im Frontend.

**Frontend (D25):** ✅ `HeightmapFilterStack`-Komponente — Filter-Liste, Toggle, Reorder ↑↓, Anwenden gegen die 6 Backend-Endpoints, Reset. Bei AI-Modus wird der Stack auf der AI-Heightmap angewandt. **Noch offen** als spaetere Iteration: Live-3D-Heightmap-Preview via Three.js DisplacementMap.

### Stufe 3: AI-basierte Tiefenbild-Generierung ✅ **Scaffolding fertig (Phase E)**

**Implementation steht** in [`stl/ai_tiefenkarte.py`](../../backend/camwosa/stl/ai_tiefenkarte.py)
als **optionales** Modul — benoetigt das `[ai]`-Extra:

```bash
pip install 'camwosa[ai]'   # 700+ MB Torch + transformers
```

Wenn das Extra nicht installiert ist, wird beim Aufruf eine klare
`AIExtraFehlt`-Exception geworfen, und der API-Endpoint liefert 422 mit
Installations-Hinweis — **kein** Crash, kein Cloud-Roundtrip.

**Modelle** (alle Open Source, lokal nach erstem Download):

| Modell | HuggingFace | Groesse | Qualitaet |
|--------|-------------|---------|-----------|
| `depth-anything-v2-small` (Default) | depth-anything/Depth-Anything-V2-Small-hf | 100 MB | gut |
| `depth-anything-v2-base` | depth-anything/Depth-Anything-V2-Base-hf | 375 MB | sehr gut |
| `midas-v3-small` | Intel/dpt-swinv2-tiny-256 | 150 MB | gut, schnell |

**API**:
```bash
# Verfuegbarkeit + Modell-Liste
curl http://localhost:8765/api/heightmap/ai/modelle

# Inferenz (nur wenn [ai] installiert)
curl -F "datei=@foto.jpg" -F "max_tiefe_mm=2" -F "modell=depth-anything-v2-small" \
     http://localhost:8765/api/heightmap/aus-bild-ai
```

Modell-Datei wird beim ersten Aufruf vom Hugging Face Hub geladen und in
`~/.cache/huggingface` gecacht. Privacy-Versprechen:
- Modell laeuft **100% lokal** nach dem Download
- Keine Telemetrie, kein Upload des Bildes
- Hugging-Face-Download kann via `HF_HUB_OFFLINE=1` blockiert werden

---

**Hintergrund (Stufe 3 Konzept):**

Carveco / VistaSculpt nutzen mittlerweile **monokulare Tiefenschaetzung**:
ein neuronales Netz (MiDaS, DPT, Depth Anything V2) leitet aus einem
gewoehnlichen Foto eine Tiefenkarte ab — was vorne/hinten ist. Das macht
Reliefs aus normalen Fotos viel besser als bloßes Helligkeits-Mapping.

**Verfuegbare Modelle (Open Source)**:
- **MiDaS v3.1** (Intel) — bewährt, schnell, PyTorch / ONNX
- **DPT** (Dense Prediction Transformer) — bessere Qualitaet
- **Depth Anything V2** — neuestes / state-of-the-art (2024)

**Implementations-Pfad**:
- PyTorch-Modell laden (~250 MB), GPU optional
- Bild durch Netz schicken → relative Tiefen-Map
- Auf Werkstueck-Tiefe skalieren
- Optional: mit klassischer Heightmap kombinieren (Glaettung etc.)

**Aufwand**: +5-7 Tage. Achtung: ~250 MB Modell-Dateien als Dependency,
PyTorch ist gross. Sollte optional sein (extra `[ai]`-Extra-Dep).

**Aufwand-Limitierung**: rein lokal, kein Cloud — passt zu CAMWOSA-Prinzipien
(no-cloud, no-tracking).

## Wrap-Kombination ✅ **fertig (Phase C)**

Wenn das Relief auf einen Zylinder gewickelt werden soll: konzeptuell einfach.

**Implementation steht** in [`cam/wrap.py`](../../backend/camwosa/cam/wrap.py) als
`erzeuge_wrap_relief_toolpath(heightmap, werkzeug, parameter)`. Parameter
(`WrapReliefParameter`):

- `werkzeug_id`, `spindel_rpm`, `vorschub`, `eintauch_vorschub`
- `werkstueck_radius_mm` (Default 20)
- `sicherheitshoehe_mm` (Default 5)
- `strategie`: `RASTER_X` (Standard, X-Bahnen) oder `RASTER_A` (A-Bahnen)
- `serpentinen` (Default True) — jede zweite Bahn rueckwaerts

**Sicherheits-Check** `pruefe_heightmap_fuer_radius(heightmap, radius)` warnt
vor:
- Y-Spanne > Werkstueck-Umfang (Design wickelt sich mehrfach um)
- Tiefe >= Radius (Fraeser geht durch die Drehachse — blockt direkt)
- Negativem oder Null-Radius (blockt direkt)

**API**:
```bash
# Erst Heightmap aus Bild bauen
curl -F "datei=@logo.png" -F "max_tiefe_mm=1.5" -F "pixel_pro_mm=3" \
     http://localhost:8765/api/heightmap/aus-bild > heightmap.json

# Dann auf Zylinder wickeln
curl -X POST http://localhost:8765/api/heightmap/wrap-relief \
     -H "Content-Type: application/json" \
     -d '{
       "heightmap": '"$(cat heightmap.json)"',
       "werkzeug_id": "kugel_3mm_2s_hm",
       "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
       "werkstueck_radius_mm": 25.0,
       "strategie": "raster_x"
     }'
```

Vorab-Check ohne Toolpath-Generierung:
```bash
curl -X POST http://localhost:8765/api/heightmap/wrap-relief/pruefen \
     -H "Content-Type: application/json" \
     -d '{"heightmap": {...}, "werkstueck_radius_mm": 25.0}'
```

---

### Mathematik (Referenz)

Vorraussetzung: Heightmap als 2D-Array Z[ix, iy] mit Pixel-Spacing `dx`/`dy`.

**Flache Bearbeitung** (Standard):
```
Werkzeug-X = ix × dx
Werkzeug-Y = iy × dy
Werkzeug-Z = max_tiefe - Z[ix, iy]   # ins Material rein
```

**Wrap-Bearbeitung** (auf Zylinder R):
```
Werkzeug-X = ix × dx                  # entlang Werkstueck-Laengsachse
Werkzeug-A = (iy × dy) × 57.296 / R   # Werkstueck-Drehwinkel
Werkzeug-Z = R - Z[ix, iy]            # ABER: relativ zur Mittel-Drehachse!
            = (R + h_oberflaeche) - tiefe[ix, iy]
```

Im G-Code:
- X-Werte = ix·dx (linear)
- Y-Werte = A° (umgemappt auf A-Achse)
- Z-Werte = Werkstueck-Radius minus Eintauchtiefe (= „Hoehe ueber Drehachse")

Das ist die **Erweiterung von wrap.py um die Z-Dimension** — wir haben
bereits die Y→A-Umrechnung und das Wrap-Konzept. Was fehlt: pro Pixel
ein Z-Wert statt eine flache Tiefe.

## Toolpath-Strategien

| Strategie | Wann |
|-----------|------|
| **Raster X/Y** ✅ (vorhanden) | Standard, einfach, gut fuer flache Reliefs |
| **Spiral** | Effizient fuer runde Reliefs, weniger Werkzeug-Anhaltepunkte |
| **Adaptive** | Werkzeug folgt den Hoehenkonturen — saubere Oberflaeche, langsamer |
| **Schrupp + Schlicht** | erst grob mit Schaftfraeser, dann Kugelfraeser fuer Detail |

Werkzeug-Form-Compensation:
- Kugelfraeser: ideal fuer Reliefs (rundet sanft)
- Schaftfraeser: nur fuer Schruppen + flache Stellen
- V-Bit: nur fuer scharfe Linien-Reliefs (PhotoVCarve-Stil)

## Komponenten die wir brauchen

| Komponente | Bestehend? | Aufwand |
|-----------|-----------|---------|
| **Heightmap-Datenmodell** (`stl/heightmap.py`) | ✅ aus STL | — |
| **Bild → Heightmap** | ❌ | 1-2 Tage |
| **Heightmap-Vorverarbeitung** (Glaetten, Kurve, Zero-Plane) | ❌ | 2-3 Tage |
| **Heightmap → Toolpath Raster** (`cam/relief.py`) | ✅ Raster X/Y | — |
| **Werkzeug-Form-Compensation** | ⚠️ teilweise | 1-2 Tage |
| **Wrap auf Zylinder** | ⚠️ wrap.py existiert, aber 2D-Pfad. Erweiterung: pro Pixel Z | 2-3 Tage |
| **Frontend: Bild-Upload + Vorschau** | ❌ | 2 Tage |
| **Frontend: Heightmap-Bearbeitung** | ❌ | 3-5 Tage |
| **Frontend: 3D-Relief-Preview** | ⚠️ Three.js da, neue Component | 1 Tag |
| **AI-Tiefen-Schaetzung** (MiDaS) | ❌ optional | 5-7 Tage |
| **Frontend: Relief-Wrap-Preview auf Zylinder** | ⚠️ wrap-preview da, fuer Heightmap erweitern | 2 Tage |

## Gesamtaufwand-Schaetzung

- **MVP (Stufe 1 + Wrap)**: ~2-3 Wochen Backend + Frontend, ohne AI
- **Volle Stufe 2** (Bearbeitung + Preview): +1-2 Wochen
- **AI** (Stufe 3): +1-2 Wochen, plus PyTorch-Dep-Management

## Ehrliche Trade-offs

**Was wir gut bauen koennen:**
- Grayscale-Heightmap → Toolpath (klassisch, vielfach implementiert)
- Wrap auf Zylinder (mathematisch sauber, Konzept klar)
- Backend-Integration in unsere bestehende Pipeline
- 3D-Preview mit Three.js

**Was wir NICHT bauen sollten:**
- Carveco-Niveau Knet-/Brush-Tools (Jahre an Polish)
- Eigenes Tiefen-Schaetzungs-Netz (nutzen wir MiDaS as-is)
- Echtzeit-GPU-Rendering eines 3D-Mesh waehrend der User editiert
  (Heightmap-Editing bleibt 2D bis zur Toolpath-Berechnung)

**Risiken / Limitierungen:**
- **Performance** bei grossen Bildern: 2000×2000 Pixel = 4 Mio Heightmap-Punkte.
  Toolpath wird riesig. Wir muessen unterabtasten oder
  Stepover-basiert reduzieren.
- **AI-Modelle** kommen mit License + Modell-Datei-Groesse + Hardware-Anforderungen.
  Sollte als Optional-Feature mit Hinweis konzipiert werden.
- **Wrap eines Reliefs** mit hoher Detail-Tiefe (>2mm) kann Werkzeug-Konflikte
  geben — Kugelfraeser laeuft im Wrap-Mode bei steilen Profilen evtl. an
  benachbarte Bereiche an. Vor Erzeugung sollten wir warnen.

## Use-Cases die das ermoeglicht

- Foto eines Kindes auf einem Holzanhaenger einlasern/fraesen
- Firmen-Logo (PNG) auf einer Drechselsaeule rundherum (Wrap)
- Karten / Reliefkarten aus Satellitenbildern
- Texturen (Holz-Maserung, Stein) als Strukturmuster ueber ein Werkstueck wickeln
- Selbstgemalte / generierte Tiefenbilder als „Geheimformel" auf eine Box

## Roadmap-Vorschlag

1. **Phase A** ✅ Grayscale-Bild → Heightmap → Relief-Toolpath (flach).
2. **Phase B** ✅ Frontend-View mit Bild-Upload, Live-Preview, Parameter-Setup.
3. **Phase C** ✅ Wrap-Kombination — Heightmap auf Zylinder gewickelt
   (Master-Plan A34, Issue [#16](https://github.com/MadGapun/CAMWOSA/issues/16)).
4. **Phase D** ✅ Bearbeitungs-Tools Backend (Gamma, Stretch, Zero-Plane,
   Edge-Boost, Selective-Smoothing, Detail-Slider) + 6 API-Endpoints.
   Frontend-Filterpanel folgt als D25 (Master-Plan A35, Issue
   [#17](https://github.com/MadGapun/CAMWOSA/issues/17)).
5. **Phase E** ✅ Scaffolding (optional `[ai]`-Extra) — Depth-Anything-V2 +
   MiDaS via HuggingFace transformers, Lazy-Import, klare Fehlermeldung wenn
   Extra fehlt. Frontend-Toggle folgt mit D25. (Master-Plan A36, Issue
   [#18](https://github.com/MadGapun/CAMWOSA/issues/18)).

## Wann starten?

Markus hat das als „mehr eine Frage als eine Anweisung" formuliert. Die
Antwort: **ja, machbar, klare Bausteine vorhanden, Phasen-weise umsetzbar**.
Wann wir starten, entscheidet er — entweder direkt nach der naechsten
Frage, oder nach anderen Prioritaeten.

## Verwandt

- [Wrap-Mode](Wrap-Mode) — die Mathematik fuer Zylinder-Projektion ist da
- [Operation-Relief](Operation-Relief) — Raster-Toolpath aus Heightmap ist da
- [STL-Import](STL-Import) — STL→Heightmap ist da, gleicher Backend-Pfad
- [Material-Abtrag-Simulation](Material-Abtrag-Simulation) — kann Reliefs simulieren

## Quellen

- [Carveco AI Image to Relief](https://learn.carveco.com/3d-design-reliefs-and-models/carveco-ai-image-to-relief/)
- [Vectric PhotoVCarve](https://www.vectric.com/products/photovcarve/)
- [PixelCNC by Deftware](https://deftware.org/pages/pixelcnc)
- [Relief Maker](https://www.reliefmaker.com/)
- [VistaSculpt](https://vistasculpt.com/) — AI-basiert
- [Sculptok](https://www.sculptok.com/) — AI-Depth-Map-Generator
- [Vectric Rotary Wrapping V12](https://docs.vectric.com/docs/V12.0/Aspire/ENU/Help/form/rotary-machining-and-wrapping/index.html)
- [MiDaS auf GitHub (Intel)](https://github.com/isl-org/MiDaS) — Open-Source-Tiefen-Schaetzung
- [Depth Anything V2 (Towards Data Science)](https://towardsdatascience.com/monocular-depth-estimation-with-depth-anything-v2-54b6775abc9f/)
- [222 Artisans: Vectric Rotary Workflow](https://www.222artisans.com/Rotary/RotaryYaxis.html)
