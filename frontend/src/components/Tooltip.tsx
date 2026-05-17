import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Drei Tooltip-Stufen nach Design-Note 7:
 *
 * 1. ``<WertTooltip>``: zeigt beim Hover an einem Wert die Quelle + Original.
 *    Sehr klein, nur Fakten, kein Pfeil-Schickschnack.
 * 2. ``<FachTooltip>``: haengt an einem ?-Icon und erklaert Fachbegriffe
 *    (Spanlast, Adaptive Clearing, Stepover, ...). Mit Definition + ggf.
 *    Formel + Sicherheits-Hinweis.
 * 3. ``<CoachMark>``: zeigt beim Erstbesuch einer View ein Pop-Hint.
 *    Dismissable per Klick, merkt sich „gesehen" in LocalStorage.
 *
 * Design-Prinzipien:
 * - Nichts blinkt, nichts ist modal, nichts blockiert den User
 * - Akzentfarbe (Orange) ist tabu — Tooltips sind grau/info-blau
 * - Auf Touch-Geraeten: tap-to-show, tap-anywhere-to-hide
 */

// ---------------------------------------------------------------------------
// Stufe 1: WertTooltip — Hover an Wert, zeigt Quelle/Original
// ---------------------------------------------------------------------------

interface WertTooltipProps {
  /** Text im Tooltip — z.B. „Material-Preset · Original: 18000 RPM" */
  inhalt: string;
  /** Element auf das gehovered wird */
  children: ReactNode;
  /** Optional: Position-Hint */
  position?: "oben" | "unten";
}

export function WertTooltip({ inhalt, children, position = "oben" }: WertTooltipProps) {
  const [offen, setOffen] = useState(false);
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOffen(true)}
      onMouseLeave={() => setOffen(false)}
      onTouchStart={() => setOffen(!offen)}
    >
      {children}
      {offen && (
        <span
          className={[
            "pointer-events-none absolute left-1/2 z-50 -translate-x-1/2 whitespace-nowrap",
            "rounded border border-camwosa-default bg-camwosa-elevated px-2 py-1",
            "font-mono text-[10px] text-camwosa-text shadow-lg",
            position === "oben" ? "bottom-full mb-1" : "top-full mt-1",
          ].join(" ")}
        >
          {inhalt}
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Stufe 2: FachTooltip — ?-Icon, klick fuer Erklaerung
// ---------------------------------------------------------------------------

interface FachTooltipProps {
  begriff: string;
  /** Kurze Definition (1-2 Saetze) */
  definition: string;
  /** Optional: Formel oder Beispiel */
  formel?: string;
  /** Optional: Sicherheits-/Praxis-Hinweis */
  hinweis?: string;
}

/** Inline-?-Icon — beim Klick erscheint ein Popover mit Erklaerung. */
export function FachTooltip({ begriff, definition, formel, hinweis }: FachTooltipProps) {
  const [offen, setOffen] = useState(false);
  const ref = useRef<HTMLSpanElement | null>(null);

  // Klick ausserhalb schliesst
  useEffect(() => {
    if (!offen) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOffen(false);
    };
    window.addEventListener("mousedown", onClick);
    return () => window.removeEventListener("mousedown", onClick);
  }, [offen]);

  return (
    <span ref={ref} className="relative inline-flex">
      <button
        type="button"
        onClick={() => setOffen(!offen)}
        className="ml-1 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-camwosa-default text-[8px] text-camwosa-muted hover:border-camwosa-info hover:text-camwosa-info"
        title={`Was ist ${begriff}?`}
        aria-label={`Erklaerung: ${begriff}`}
      >
        ?
      </button>
      {offen && (
        <span
          className="absolute left-0 top-5 z-50 w-64 rounded border border-camwosa-info/40 bg-camwosa-elevated p-2 text-xs shadow-lg"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="mb-1 font-semibold text-camwosa-info">{begriff}</div>
          <div className="text-camwosa-text">{definition}</div>
          {formel && (
            <div className="mt-1 font-mono text-[10px] text-camwosa-muted">{formel}</div>
          )}
          {hinweis && (
            <div className="mt-1 border-l-2 border-camwosa-warn pl-2 text-[10px] text-camwosa-text">
              ⚠ {hinweis}
            </div>
          )}
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Stufe 3: CoachMark — Erstbesuch-Hint, dismissable, persistent
// ---------------------------------------------------------------------------

interface CoachMarkProps {
  /** Eindeutige ID — die „gesehen"-Markierung haengt daran */
  id: string;
  /** Kurzer Hinweis (1-2 Saetze) */
  text: string;
  /** Element auf das der Hint zeigt */
  children: ReactNode;
  /** Optional: nur an bestimmten Tag zeigen (z.B. nur 1x pro 30 Tage) */
  ablauf_tage?: number;
}

const COACH_PREFIX = "camwosa.coach.";

function coachGesehen(id: string, ablauf_tage?: number): boolean {
  if (typeof window === "undefined") return true;
  const raw = window.localStorage.getItem(COACH_PREFIX + id);
  if (!raw) return false;
  if (!ablauf_tage) return true;
  const seenAt = parseInt(raw, 10);
  if (isNaN(seenAt)) return false;
  const tageVergangen = (Date.now() - seenAt) / (1000 * 60 * 60 * 24);
  return tageVergangen < ablauf_tage;
}

function coachMerken(id: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(COACH_PREFIX + id, String(Date.now()));
}

export function CoachMark({ id, text, children, ablauf_tage }: CoachMarkProps) {
  const [zeigen, setZeigen] = useState(() => !coachGesehen(id, ablauf_tage));

  function dismiss() {
    coachMerken(id);
    setZeigen(false);
  }

  return (
    <span className="relative inline-flex">
      {children}
      {zeigen && (
        <span className="absolute left-0 top-full z-40 mt-2 w-72 rounded-lg border-2 border-camwosa-info bg-camwosa-elevated p-3 text-xs shadow-lg">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-wider text-camwosa-info">
              Tipp
            </span>
            <button
              onClick={dismiss}
              className="text-camwosa-muted hover:text-camwosa-text"
              title="Verstanden — Hint nicht mehr zeigen"
            >
              ×
            </button>
          </div>
          <div className="text-camwosa-text">{text}</div>
        </span>
      )}
    </span>
  );
}

/** Helper fuer Tests / Reset-Funktionalitaet im EinstellungenView */
export function coachMarksZuruecksetzen() {
  if (typeof window === "undefined") return;
  const keys: string[] = [];
  for (let i = 0; i < window.localStorage.length; i++) {
    const k = window.localStorage.key(i);
    if (k?.startsWith(COACH_PREFIX)) keys.push(k);
  }
  for (const k of keys) window.localStorage.removeItem(k);
}
