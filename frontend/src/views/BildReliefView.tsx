import { useEffect, useRef, useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";
import HeightmapPreview, { dekodiereZValues } from "../components/HeightmapPreview";
import HeightmapFilterStack from "../components/HeightmapFilterStack";
import { CoachMark } from "../components/Tooltip";

type Heightmap = Awaited<ReturnType<typeof camwosaApi.bildZuHeightmap>>;

/**
 * Bild-zu-Relief Phase B-View.
 *
 * Workflow:
 * 1. Bild auswählen (Drag&Drop oder File-Picker)
 * 2. Parameter setzen (max_tiefe, aufloesung, glaetten, invertieren, zero-plane)
 * 3. „Heightmap generieren" → Backend rechnet, Preview-Canvas zeigt das Ergebnis
 * 4. Werkzeug + Schnitt-Parameter wählen
 * 5. „Toolpath erzeugen" → ruft `/api/operations/relief` und legt im App-Store ab
 *
 * Hinweis: die Toolpath-Erzeugung selbst nutzt den bestehenden Relief-
 * Generator (cam/relief.py). Das hier ist die UI darum herum.
 */
export default function BildReliefView() {
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const operationHinzufuegen = useAppStore((s) => s.operationHinzufuegen);

  const [datei, setDatei] = useState<File | null>(null);
  const [bildVorschau, setBildVorschau] = useState<string | null>(null);
  const [heightmap, setHeightmap] = useState<Heightmap | null>(null);
  /** Nach Filter-Stack: die gefilterte Heightmap. Default = identisch zu heightmap. */
  const [gefilterteHeightmap, setGefilterteHeightmap] = useState<Heightmap | null>(null);
  const [busy, setBusy] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  // Parameter
  const [maxTiefe, setMaxTiefe] = useState(2.0);
  const [pixelProMm, setPixelProMm] = useState(4.0);
  const [invertieren, setInvertieren] = useState(false);
  const [glaetten, setGlaetten] = useState(0);
  const [zeroPlane, setZeroPlane] = useState(0);
  const [maxDim, setMaxDim] = useState<number | "">(500);

  // AI-Toggle (Phase E)
  const [aiModus, setAiModus] = useState(false);
  const [aiVerfuegbar, setAiVerfuegbar] = useState<boolean | null>(null);
  const [aiModell, setAiModell] = useState<string>("depth-anything-v2-small");
  const [aiModelle, setAiModelle] = useState<Array<{id: string; label: string}>>([]);

  // Beim ersten Render: AI-Status abfragen
  useEffect(() => {
    void camwosaApi.aiModelle().then((info) => {
      setAiVerfuegbar(info.ist_installiert);
      setAiModell(info.default);
      setAiModelle(
        Object.entries(info.modelle).map(([id, m]) => ({
          id,
          label: `${id} (${m.groesse_mb} MB, ${m.qualitaet})`,
        })),
      );
    }).catch(() => setAiVerfuegbar(false));
  }, []);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!datei) {
      setBildVorschau(null);
      return;
    }
    const url = URL.createObjectURL(datei);
    setBildVorschau(url);
    return () => URL.revokeObjectURL(url);
  }, [datei]);

  async function generiereHeightmap() {
    if (!datei) { setFehler("Bitte zuerst ein Bild waehlen"); return; }
    setBusy(true); setFehler(null);
    try {
      let r: Heightmap;
      if (aiModus) {
        r = (await camwosaApi.bildZuHeightmapAi(datei, {
          max_tiefe_mm: maxTiefe,
          pixel_pro_mm: pixelProMm,
          modell: aiModell,
          invertieren,
          max_dimension_px: typeof maxDim === "number" ? maxDim : undefined,
        })) as Heightmap;
      } else {
        r = await camwosaApi.bildZuHeightmap(datei, {
          max_tiefe_mm: maxTiefe,
          pixel_pro_mm: pixelProMm,
          invertieren,
          glaetten_radius: glaetten,
          zero_plane_schwelle: zeroPlane,
          max_dimension_px: typeof maxDim === "number" ? maxDim : null,
        });
      }
      setHeightmap(r);
      setGefilterteHeightmap(r);  // Filter-Stack resettet sich automatisch
    } catch (e: any) {
      setFehler(e.response?.data?.fehler ?? e.message ?? "Heightmap-Generierung fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  function dateiGewaehlt(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setDatei(f);
  }

  function dropHandler(e: React.DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) setDatei(f);
  }

  // Anzuzeigende Heightmap: bevorzugt die gefilterte Variante
  const sichtbar = gefilterteHeightmap ?? heightmap;
  const zValues = sichtbar
    ? dekodiereZValues(sichtbar.z_values_base64)
    : null;

  return (
    <div className="space-y-4">
      <header>
        <CoachMark
          id="bild_relief_intro"
          text="Lade ein Bild hoch, der Backend macht daraus eine Heightmap. Helle Stellen = hoch, dunkle = tief (umkehrbar). Danach kannst du daraus einen Relief-Toolpath erzeugen."
          ablauf_tage={60}
        >
          <h1 className="text-xl font-bold">Bild → Relief</h1>
        </CoachMark>
        <p className="text-sm text-camwosa-muted">
          Bild → Heightmap → Filter-Stack → Toolpath. AI-Tiefenschaetzung
          (Phase E) optional bei installiertem <code>[ai]</code>-Extra.
          Wickeln auf Zylinder via Wrap-View.
        </p>
      </header>

      {/* Bild-Upload */}
      <section
        className="rounded border-2 border-dashed border-camwosa-default bg-camwosa-surface p-6 text-center"
        onDragOver={(e) => e.preventDefault()}
        onDrop={dropHandler}
      >
        {bildVorschau ? (
          <div className="flex flex-col items-center gap-2">
            <img
              src={bildVorschau}
              alt="Vorschau"
              className="max-h-48 rounded border border-camwosa-default"
            />
            <div className="text-xs text-camwosa-muted">
              {datei?.name} · {datei && Math.round(datei.size / 1024)} KB
            </div>
            <button
              className="rounded border border-camwosa-default px-3 py-1 text-xs hover:bg-camwosa-overlay"
              onClick={() => { setDatei(null); setHeightmap(null); }}
            >
              Anderes Bild
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-camwosa-muted">
              Bild hierhin ziehen oder waehlen (PNG, JPG, GIF, ...)
            </p>
            <button
              className="rounded bg-camwosa-accent px-4 py-2 font-medium text-camwosa-bg hover:opacity-90"
              onClick={() => fileInputRef.current?.click()}
            >
              Bild waehlen
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={dateiGewaehlt}
              className="hidden"
            />
          </div>
        )}
      </section>

      {/* Modus-Wahl Klassisch vs. AI */}
      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Verfahren</h2>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <label className="flex items-center gap-1">
            <input
              type="radio"
              name="hm_modus"
              checked={!aiModus}
              onChange={() => setAiModus(false)}
            />
            <span>Klassisch (Helligkeits-Mapping)</span>
          </label>
          <label className={`flex items-center gap-1 ${aiVerfuegbar === false ? "opacity-60" : ""}`}>
            <input
              type="radio"
              name="hm_modus"
              checked={aiModus}
              disabled={aiVerfuegbar === false}
              onChange={() => setAiModus(true)}
            />
            <span>
              AI-Tiefenschaetzung
              {aiVerfuegbar === false && (
                <span className="ml-1 text-camwosa-warn">
                  (Extra nicht installiert: <code>pip install camwosa[ai]</code>)
                </span>
              )}
              {aiVerfuegbar === null && (
                <span className="ml-1 text-camwosa-muted">(Status laed...)</span>
              )}
            </span>
          </label>
          {aiModus && aiVerfuegbar && aiModelle.length > 0 && (
            <label className="ml-2">
              <span className="mr-1 text-camwosa-muted">Modell:</span>
              <select
                value={aiModell}
                onChange={(e) => setAiModell(e.target.value)}
                className="rounded border border-camwosa-default bg-camwosa-bg px-2 py-1"
              >
                {aiModelle.map((m) => (
                  <option key={m.id} value={m.id}>{m.label}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </section>

      {/* Parameter */}
      <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
        <h2 className="mb-2 text-sm font-semibold">Heightmap-Parameter</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Num label="Max-Tiefe (mm)" v={maxTiefe} on={setMaxTiefe} step={0.1} min={0.1} />
          <Num label="Pixel/mm (Aufloesung)" v={pixelProMm} on={setPixelProMm} step={0.5} min={0.5} />
          <Num label="Glaetten-Radius (Pixel)" v={glaetten} on={(n) => setGlaetten(Math.max(0, Math.round(n)))} step={1} min={0} max={10} />
          <Num label="Zero-Plane-Schwelle (0-1)" v={zeroPlane} on={setZeroPlane} step={0.05} min={0} max={1} />
          <label className="text-xs">
            <span className="mb-0.5 block text-camwosa-muted">Max-Dimension (Pixel)</span>
            <input
              type="number"
              value={maxDim}
              onChange={(e) => setMaxDim(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="leer = original"
              className="w-full rounded bg-camwosa-bg px-2 py-1"
            />
          </label>
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={invertieren}
              onChange={(e) => setInvertieren(e.target.checked)}
            />
            <span>Invertieren (dunkel = hoch)</span>
          </label>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button
            className="rounded bg-camwosa-accent px-4 py-2 font-medium text-camwosa-bg hover:opacity-90 disabled:opacity-50"
            onClick={() => void generiereHeightmap()}
            disabled={!datei || busy}
          >
            {busy ? "Berechne..." : "→ Heightmap generieren"}
          </button>
          {heightmap && (
            <span className="text-xs text-camwosa-ok">
              ✓ {heightmap.statistik.shape_x}×{heightmap.statistik.shape_y} Pixel ·{" "}
              {heightmap.statistik.breite_mm.toFixed(1)}×{heightmap.statistik.hoehe_mm.toFixed(1)} mm ·{" "}
              max Tiefe {heightmap.statistik.max_tiefe_mm.toFixed(2)} mm
            </span>
          )}
        </div>
      </section>

      {fehler && (
        <div className="rounded border border-red-700 bg-red-900/30 p-2 text-xs text-red-300">
          {fehler}
        </div>
      )}

      {/* Preview */}
      {sichtbar && zValues && (
        <section className="rounded border border-camwosa-default bg-camwosa-surface p-3">
          <h2 className="mb-2 text-sm font-semibold">
            Heightmap-Preview
            <span className="ml-2 text-xs font-normal text-camwosa-muted">
              weiss = Oberflaeche · schwarz = max Tiefe
              {gefilterteHeightmap && gefilterteHeightmap !== heightmap && (
                <span className="ml-2 text-camwosa-accent">· nach Filter-Stack</span>
              )}
            </span>
          </h2>
          <HeightmapPreview
            zValues={zValues}
            shape={sichtbar.shape}
            maxTiefeMm={sichtbar.statistik.max_tiefe_mm || 1}
            hoehe={360}
          />
          <p className="mt-2 text-xs text-camwosa-muted">
            Statistik: Z von <span className="font-mono">{sichtbar.statistik.z_min.toFixed(2)}</span> bis{" "}
            <span className="font-mono">{sichtbar.statistik.z_max.toFixed(2)}</span> mm,
            Mittel <span className="font-mono">{sichtbar.statistik.z_mittel.toFixed(2)}</span> mm.
            {sichtbar.statistik.anzahl_pixel > 1_000_000 && (
              <span className="ml-2 text-camwosa-warn">
                ⚠ {sichtbar.statistik.anzahl_pixel.toLocaleString("de-DE")} Pixel — Toolpath wird gross,
                Max-Dimension reduzieren oder gröberen Pixel/mm-Wert waehlen.
              </span>
            )}
          </p>
        </section>
      )}

      {/* Filter-Stack (Master-Plan D25 / Phase D) */}
      {heightmap && (
        <HeightmapFilterStack
          originalHeightmap={heightmap}
          onErgebnis={(g) => setGefilterteHeightmap(g as Heightmap)}
        />
      )}

      {heightmap && (
        <div className="rounded border border-camwosa-info/40 bg-info-soft p-3 text-xs text-camwosa-text">
          💡 Nächster Schritt: Diese Heightmap wird vom Relief-Toolpath-Generator
          ([cam/relief.py](https://github.com/MadGapun/CAMWOSA/blob/main/backend/camwosa/cam/relief.py))
          zu G-Code verarbeitet. Frontend-Knopf dafuer kommt in der naechsten
          Iteration — fuer jetzt: ueber den ApiClient `opRelief(...)` direkt,
          oder via MCP von Claude aus.
        </div>
      )}
    </div>
  );
}

function Num({
  label, v, on, step, min, max,
}: { label: string; v: number; on: (n: number) => void; step: number; min?: number; max?: number }) {
  return (
    <label className="text-xs">
      <span className="mb-0.5 block text-camwosa-muted">{label}</span>
      <input
        type="number"
        value={v}
        step={step}
        min={min} max={max}
        onChange={(e) => on(Number(e.target.value))}
        className="w-full rounded bg-camwosa-bg px-2 py-1"
      />
    </label>
  );
}
