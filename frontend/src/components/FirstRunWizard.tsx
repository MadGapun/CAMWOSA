import { useEffect, useState } from "react";
import { camwosaApi } from "../api/client";
import { useAppStore } from "../state/store";

/**
 * First-Run-Wizard nach Design-Note 6 (Design Exploration):
 * „CAMWOSA fokussiert auf die 4 Dinge die du einmal machst:
 *  Maschine, Spindel, ein Werkzeug, Materialien."
 *
 * Erscheint EINMALIG beim ersten Start, wenn keine aktive Maschine im Store ist.
 * Stellt 4 simple Auswahlen, schreibt sie in den Store + LocalStorage und
 * verschwindet dann. User kann ihn ueber „Einstellungen → Onboarding nochmal
 * zeigen" wieder oeffnen.
 */
const WIZARD_DONE_KEY = "camwosa.firstRunDone";

export default function FirstRunWizard({
  onClose,
}: { onClose: () => void }) {
  const maschinen = useAppStore((s) => s.maschinen);
  const spindeln = useAppStore((s) => s.spindeln);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const materialien = useAppStore((s) => s.materialien);
  const setAktiveMaschine = useAppStore((s) => s.setAktiveMaschine);
  const setAktiveSpindelId = useAppStore((s) => s.setAktiveSpindelId);
  const setAktivesMaterial = useAppStore((s) => s.setAktivesMaterial);

  const [schritt, setSchritt] = useState(0);
  const [maschineId, setMaschineId] = useState("");
  const [spindelId, setSpindelId] = useState("");
  const [werkzeugId, setWerkzeugId] = useState("");
  const [materialId, setMaterialId] = useState("");

  // Spindel-Filter abhaengig von gewaehlter Maschine
  const verfuegbareSpindeln = maschineId
    ? spindeln.filter((sp) =>
        maschinen.find((m) => m.id === maschineId)?.spindel_ids?.includes(sp.id),
      )
    : spindeln;

  function fertig() {
    setAktiveMaschine(maschineId || null);
    if (spindelId) setAktiveSpindelId(spindelId);
    if (materialId) setAktivesMaterial(materialId);
    window.localStorage.setItem(WIZARD_DONE_KEY, "true");
    onClose();
  }

  const schritte = [
    {
      titel: "1 · Maschine",
      hinweis: "Welche CNC nutzt du? Bei mehreren waehlst du die, mit der du gleich loslegen willst — kannst spaeter wechseln.",
      auswahl: (
        <Liste
          eintraege={maschinen.map((m) => ({
            id: m.id,
            titel: m.name,
            details: `${m.hersteller} ${m.modell} · Arbeitsraum ${m.arbeitsraum.x}×${m.arbeitsraum.y}×${m.arbeitsraum.z}mm`,
          }))}
          aktiv={maschineId}
          onWaehlen={setMaschineId}
        />
      ),
      kannWeiter: !!maschineId,
    },
    {
      titel: "2 · Spindel",
      hinweis: "ProVerXL hat oft zwei Spindeln (OEM-Router + Makita-Upgrade). Welche ist gerade montiert?",
      auswahl: (
        <Liste
          eintraege={verfuegbareSpindeln.map((sp) => ({
            id: sp.id,
            titel: sp.name,
            details: `${sp.hersteller} ${sp.modell} · ${sp.rpm_min}-${sp.rpm_max} RPM · Typ: ${sp.typ}`,
          }))}
          aktiv={spindelId}
          onWaehlen={setSpindelId}
        />
      ),
      kannWeiter: !!spindelId,
    },
    {
      titel: "3 · Erstes Werkzeug",
      hinweis: "Welches Werkzeug spannst du als erstes ein? Du kannst spaeter beliebig viele anlegen.",
      auswahl: (
        <Liste
          eintraege={werkzeuge.map((w) => ({
            id: w.id,
            titel: w.name,
            details: `${w.typ} · Ø ${w.durchmesser}mm · ${w.schneiden} Schneiden`,
          }))}
          aktiv={werkzeugId}
          onWaehlen={setWerkzeugId}
        />
      ),
      kannWeiter: !!werkzeugId,
    },
    {
      titel: "4 · Material",
      hinweis: "Womit faengst du an? Bestimmt die Standard-Feeds & Speeds fuer dein erstes Projekt.",
      auswahl: (
        <Liste
          eintraege={materialien.map((m) => ({
            id: m.id,
            titel: m.name,
            details: `${m.kategorie}${m.unter_kategorie ? " · " + m.unter_kategorie : ""}`,
          }))}
          aktiv={materialId}
          onWaehlen={setMaterialId}
        />
      ),
      kannWeiter: !!materialId,
    },
  ];

  const aktuell = schritte[schritt];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-lg border border-camwosa-default bg-camwosa-elevated shadow-lg">
        <header className="border-b border-camwosa-default p-4">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-camwosa-accent">
            Erst-Setup
          </div>
          <h2 className="text-lg font-semibold">{aktuell.titel}</h2>
          <p className="mt-1 text-xs text-camwosa-muted">{aktuell.hinweis}</p>
        </header>

        <div className="flex-1 overflow-auto p-4">
          {aktuell.auswahl}
        </div>

        <footer className="flex items-center justify-between gap-2 border-t border-camwosa-default p-3">
          <div className="flex gap-1">
            {schritte.map((_, i) => (
              <span
                key={i}
                className={`h-1.5 w-8 rounded ${
                  i < schritt
                    ? "bg-camwosa-accent"
                    : i === schritt
                    ? "bg-camwosa-accent/60"
                    : "bg-camwosa-default"
                }`}
              />
            ))}
          </div>
          <div className="flex gap-2">
            <button
              className="rounded border border-camwosa-default px-3 py-1 text-xs hover:bg-camwosa-overlay"
              onClick={onClose}
            >
              Spaeter
            </button>
            {schritt > 0 && (
              <button
                className="rounded border border-camwosa-default px-3 py-1 text-xs hover:bg-camwosa-overlay"
                onClick={() => setSchritt(schritt - 1)}
              >
                ← Zurueck
              </button>
            )}
            {schritt < schritte.length - 1 ? (
              <button
                className="rounded bg-camwosa-accent px-4 py-1 text-xs font-medium text-camwosa-bg disabled:opacity-50"
                onClick={() => setSchritt(schritt + 1)}
                disabled={!aktuell.kannWeiter}
              >
                Weiter →
              </button>
            ) : (
              <button
                className="rounded bg-camwosa-accent px-4 py-1 text-xs font-medium text-camwosa-bg disabled:opacity-50"
                onClick={fertig}
                disabled={!aktuell.kannWeiter}
              >
                ✓ Fertig
              </button>
            )}
          </div>
        </footer>
      </div>
    </div>
  );
}

function Liste({
  eintraege, aktiv, onWaehlen,
}: {
  eintraege: Array<{ id: string; titel: string; details: string }>;
  aktiv: string;
  onWaehlen: (id: string) => void;
}) {
  if (!eintraege.length) {
    return (
      <p className="text-xs text-camwosa-muted">
        Keine Eintraege gefunden — Stammdaten werden noch geladen oder
        sind leer. Du kannst den Wizard spaeter wieder oeffnen.
      </p>
    );
  }
  return (
    <ul className="space-y-1.5">
      {eintraege.map((e) => (
        <li key={e.id}>
          <button
            onClick={() => onWaehlen(e.id)}
            className={`w-full rounded border p-3 text-left text-sm transition ${
              aktiv === e.id
                ? "border-camwosa-accent bg-camwosa-accent-soft"
                : "border-camwosa-default bg-camwosa-surface hover:border-camwosa-accent/60"
            }`}
          >
            <div className="font-medium">{e.titel}</div>
            <div className="text-xs text-camwosa-muted">{e.details}</div>
          </button>
        </li>
      ))}
    </ul>
  );
}

/** Hilfsfunktion: hat der User den Wizard schon einmal abgeschlossen? */
export function firstRunErledigt(): boolean {
  if (typeof window === "undefined") return true;
  return window.localStorage.getItem(WIZARD_DONE_KEY) === "true";
}

/** Wizard erneut zeigen lassen (vom Einstellungen-View). */
export function firstRunZuruecksetzen() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(WIZARD_DONE_KEY);
  }
}
