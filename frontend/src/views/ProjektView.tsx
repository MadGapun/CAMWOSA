import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";
import { useProjektStore } from "../state/projektStore";
import {
  projektLaden,
  projektNeu,
  projektSpeichern,
  projektSpeichernAls,
} from "../state/projektIO";
import { useVarianteStore } from "../state/varianteStore";
import CADImportDialog from "../components/CADImportDialog";
import RohmaterialEditor from "../components/RohmaterialEditor";

export default function ProjektView() {
  const { t } = useTranslation();
  const maschinen = useAppStore((s) => s.maschinen);
  const materialien = useAppStore((s) => s.materialien);
  const aktiveMaschineId = useAppStore((s) => s.aktiveMaschineId);
  const setAktiveMaschine = useAppStore((s) => s.setAktiveMaschine);
  const aktivesMaterialId = useAppStore((s) => s.aktivesMaterialId);
  const setAktivesMaterial = useAppStore((s) => s.setAktivesMaterial);
  const geometrien = useAppStore((s) => s.geometrien);
  const operationen = useAppStore((s) => s.operationen);
  const geometrienLeeren = useAppStore((s) => s.geometrienLeeren);
  const spindeln = useAppStore((s) => s.spindeln);
  const aktiveSpindelId = useAppStore((s) => s.aktiveSpindelId);
  const setAktiveSpindelId = useAppStore((s) => s.setAktiveSpindelId);

  const aktiveMaschine = maschinen.find((m) => m.id === aktiveMaschineId);
  const verfuegbareSpindeln = aktiveMaschine
    ? spindeln.filter((sp) => aktiveMaschine.spindel_ids.includes(sp.id))
    : [];
  const effektiveSpindelId =
    aktiveSpindelId ?? aktiveMaschine?.aktive_spindel_id ?? null;

  const [dxfOffen, setDxfOffen] = useState(false);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("projekt.titel")}</h1>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">{t("maschine.auswahl")}</h2>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="mb-1 block text-xs text-camwosa-muted">
              {t("maschine.titel")}
            </label>
            <select
              className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm"
              value={aktiveMaschineId ?? ""}
              onChange={(e) => {
                setAktiveMaschine(e.target.value || null);
                setAktiveSpindelId(null);  // Override loeschen, Maschinen-Default greift
              }}
            >
              <option value="">— bitte waehlen —</option>
              {maschinen.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-camwosa-muted">
              Spindel
              {aktiveSpindelId === null && aktiveMaschine?.aktive_spindel_id && (
                <span className="ml-1 text-[10px]">(Default aus Maschine)</span>
              )}
            </label>
            <select
              className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm disabled:opacity-50"
              value={effektiveSpindelId ?? ""}
              disabled={!aktiveMaschine || verfuegbareSpindeln.length === 0}
              onChange={(e) => setAktiveSpindelId(e.target.value || null)}
            >
              {verfuegbareSpindeln.length === 0 && (
                <option value="">— keine Spindeln zugeordnet —</option>
              )}
              {verfuegbareSpindeln.map((sp) => (
                <option key={sp.id} value={sp.id}>
                  {sp.name} ({sp.rpm_min}–{sp.rpm_max} RPM)
                </option>
              ))}
            </select>
            {aktiveSpindelId !== null && (
              <button
                className="mt-1 text-[10px] text-camwosa-muted hover:text-camwosa-accent"
                onClick={() => setAktiveSpindelId(null)}
              >
                ↺ auf Maschinen-Default zuruecksetzen
              </button>
            )}
          </div>
          <div>
            <label className="mb-1 block text-xs text-camwosa-muted">Material</label>
            <select
              className="w-full rounded bg-camwosa-bg px-3 py-2 text-sm"
              value={aktivesMaterialId ?? ""}
              onChange={(e) => setAktivesMaterial(e.target.value || null)}
            >
              <option value="">— bitte waehlen —</option>
              {materialien.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Rohmaterial</h2>
        <RohmaterialEditor />
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Geometrie</h2>
        <div className="flex items-center gap-3">
          <button
            className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white"
            onClick={() => setDxfOffen(true)}
          >
            CAD importieren
          </button>
          {geometrien.length > 0 && (
            <>
              <span className="text-sm text-camwosa-muted">
                {geometrien.length} Objekte geladen (
                {geometrien.filter((g) => g.geschlossen).length} geschlossen)
              </span>
              <button
                className="text-xs text-camwosa-muted hover:text-camwosa-danger"
                onClick={geometrienLeeren}
              >
                Loeschen
              </button>
            </>
          )}
        </div>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-2 font-semibold">Operationen</h2>
        {operationen.length === 0 ? (
          <p className="text-sm text-camwosa-muted">
            Noch keine Operationen. Wechsle zu „Operationen" um eine anzulegen.
          </p>
        ) : (
          <ul className="space-y-1 text-sm">
            {operationen.map((op) => (
              <li key={op.id} className="flex items-center justify-between">
                <span>
                  <span className="text-camwosa-muted">{op.typ}:</span> {op.name}
                </span>
                <span className="text-xs text-camwosa-muted">
                  {op.toolpath ? `${op.toolpath.bewegungen.length} Bew.` : "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ProjektPersistenzPanel />

      <CADImportDialog open={dxfOffen} onClose={() => setDxfOffen(false)} />
    </div>
  );
}


/**
 * Projekt-Speichern/Laden-Panel (Master-Plan D4).
 *
 * Buttons: Neu, Oeffnen, Speichern, Speichern als — plus Dateiname-Anzeige
 * und Liste der zuletzt verwendeten Projekte (aus localStorage).
 */
function ProjektPersistenzPanel() {
  const { t } = useTranslation();
  const dateiname = useProjektStore((s) => s.dateiname);
  const autor = useProjektStore((s) => s.autor);
  const dirty = useProjektStore((s) => s.dirty);
  const zuletzt = useProjektStore((s) => s.zuletzt_geoeffnet);
  const setAutor = useProjektStore((s) => s.setAutor);
  const aktiveMaschineId = useAppStore((s) => s.aktiveMaschineId);
  const anzahlVarianten = useVarianteStore((s) => s.varianten.length);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [meldung, setMeldung] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleNeu() {
    if (dirty && !window.confirm(
      "Aktuelles Projekt enthaelt ungespeicherte Aenderungen. Trotzdem neues Projekt anlegen?",
    )) return;
    const name = window.prompt("Name des neuen Projekts?", "Unbenanntes Projekt");
    if (name === null) return;
    projektNeu(name);
    setMeldung(`Neues Projekt „${name}" angelegt.`);
    setFehler(null);
  }

  async function handleSpeichern() {
    if (!aktiveMaschineId) {
      setFehler("Bitte erst eine Maschine waehlen, dann kann gespeichert werden.");
      return;
    }
    setBusy(true);
    setFehler(null);
    try {
      await projektSpeichern();
      setMeldung(`Gespeichert als ${dateiname || "Unbenanntes Projekt"}.cwp`);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleSpeichernAls() {
    const neu = window.prompt("Dateiname (ohne .cwp)?", dateiname || "MeinProjekt");
    if (!neu) return;
    setBusy(true);
    setFehler(null);
    try {
      await projektSpeichernAls(neu);
      setMeldung(`Gespeichert als ${neu}.cwp`);
    } catch (e) {
      setFehler(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleOeffnen() {
    fileInputRef.current?.click();
  }

  async function handleDatei(e: React.ChangeEvent<HTMLInputElement>) {
    const datei = e.target.files?.[0];
    if (!datei) return;
    if (dirty && !window.confirm(
      "Aktuelles Projekt enthaelt ungespeicherte Aenderungen. Trotzdem ueberschreiben?",
    )) {
      e.target.value = "";
      return;
    }
    setBusy(true);
    setFehler(null);
    try {
      await projektLaden(datei);
      setMeldung(`Geladen: ${datei.name}`);
    } catch (err) {
      setFehler(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
      e.target.value = "";  // damit gleiche Datei erneut auswaehlbar ist
    }
  }

  return (
    <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <h2 className="font-semibold">{t("projekt.titel")}</h2>
        <span className="text-xs text-camwosa-muted">
          {dateiname ? `${dateiname}.cwp` : "— neu —"}
          {dirty && <span className="ml-1 text-camwosa-warn">●</span>}
          <span className="ml-2">({anzahlVarianten} Varianten)</span>
        </span>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <button
          className="rounded bg-camwosa-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          onClick={handleNeu}
          disabled={busy}
        >
          {t("projekt.neu")}
        </button>
        <button
          className="rounded border border-gray-600 px-4 py-2 text-sm hover:bg-camwosa-bg disabled:opacity-50"
          onClick={handleOeffnen}
          disabled={busy}
        >
          {t("projekt.oeffnen")}
        </button>
        <button
          className="rounded border border-camwosa-accent bg-camwosa-accent-soft px-4 py-2 text-sm font-medium text-camwosa-accent hover:opacity-90 disabled:opacity-50"
          onClick={handleSpeichern}
          disabled={busy || !aktiveMaschineId}
          title={!aktiveMaschineId ? "Erst Maschine waehlen" : "Speichern als .cwp"}
        >
          {t("projekt.speichern")}
        </button>
        <button
          className="rounded border border-gray-600 px-4 py-2 text-sm hover:bg-camwosa-bg disabled:opacity-50"
          onClick={handleSpeichernAls}
          disabled={busy || !aktiveMaschineId}
        >
          {t("projekt.speichern_als")}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".cwp,application/zip"
          onChange={handleDatei}
          className="hidden"
        />
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <label>
          <span className="text-camwosa-muted">{t("projekt.autor")}</span>
          <input
            type="text"
            value={autor}
            onChange={(e) => setAutor(e.target.value)}
            className="w-full rounded border border-camwosa-default bg-camwosa-bg px-2 py-1"
            placeholder="Dein Name"
          />
        </label>
        {zuletzt.length > 0 && (
          <div>
            <span className="text-camwosa-muted">Zuletzt geoeffnet:</span>
            <ul className="mt-1 list-disc pl-4 text-camwosa-text">
              {zuletzt.slice(0, 5).map((p) => (
                <li key={p}>{p}.cwp</li>
              ))}
            </ul>
            <span className="text-[10px] text-camwosa-muted">
              (Liste — Browser muss .cwp-Datei selbst auswaehlen)
            </span>
          </div>
        )}
      </div>

      {meldung && (
        <p className="mt-2 text-xs text-camwosa-ok">{meldung}</p>
      )}
      {fehler && (
        <p className="mt-2 text-xs text-camwosa-danger">⚠ {fehler}</p>
      )}
    </section>
  );
}
