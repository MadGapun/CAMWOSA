import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";
import { camwosaApi } from "../api/client";
import type { MachineBundle, Spindel } from "../api/types";
import Modal from "../components/Modal";
import SpindelEditor from "../editor/SpindelEditor";

const HERKUNFT_LABEL: Record<string, string> = {
  oem: "OEM",
  upgrade: "Upgrade",
  eigenbau: "Eigenbau",
};

export default function MaschinenView() {
  const { t } = useTranslation();
  const maschinen = useAppStore((s) => s.maschinen);
  const spindeln = useAppStore((s) => s.spindeln);
  const setSpindeln = useAppStore((s) => s.setSpindeln);
  const aktiveSpindelId = useAppStore((s) => s.aktiveSpindelId);
  const setAktiveSpindelId = useAppStore((s) => s.setAktiveSpindelId);
  const [importFehler, setImportFehler] = useState<string | null>(null);
  const [importOk, setImportOk] = useState<string | null>(null);
  const [spEdit, setSpEdit] = useState<"none" | "neu" | "bearbeiten">("none");
  const [spDetail, setSpDetail] = useState<Spindel | null>(null);

  async function reloadSpindeln() {
    setSpindeln(await camwosaApi.spindeln());
  }

  async function spindelLoeschen(sp: Spindel) {
    if (!window.confirm(`Spindel '${sp.name}' wirklich loeschen?`)) return;
    try {
      await camwosaApi.spindelLoeschen(sp.id);
      await reloadSpindeln();
    } catch (e: any) {
      window.alert(`Loeschen fehlgeschlagen: ${e.response?.data?.fehler ?? e.message}`);
    }
  }

  async function exportMaschine(id: string) {
    const bundle = await camwosaApi.machineExport(id);
    const blob = new Blob([JSON.stringify(bundle, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${id}.camwosa-machine.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function importMaschine(file: File) {
    setImportFehler(null);
    setImportOk(null);
    try {
      const txt = await file.text();
      const bundle = JSON.parse(txt) as MachineBundle;
      const res = await camwosaApi.machineImport(bundle);
      if (res.gueltig) {
        setImportOk(
          `Maschine "${res.maschine.name}" mit ${res.spindeln.length} Spindel(n) validiert. ` +
          `Zum dauerhaften Speichern Datei in data/machines/community/ ablegen.`
        );
      } else {
        setImportFehler(res.fehler ?? "Unbekannter Fehler");
      }
    } catch (e: unknown) {
      setImportFehler(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("navigation.maschinen")}</h1>
        <label className="cursor-pointer rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-white">
          Bundle importieren
          <input
            type="file"
            accept=".json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void importMaschine(f);
            }}
          />
        </label>
      </div>

      {importOk && (
        <div className="rounded border border-camwosa-ok bg-green-950/20 p-2 text-xs text-camwosa-ok">
          {importOk}
        </div>
      )}
      {importFehler && (
        <div className="rounded border border-camwosa-danger bg-red-950/30 p-2 text-xs text-camwosa-danger">
          {importFehler}
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {maschinen.map((m) => {
          // Effektiv aktive Spindel: Session-Override (Projekt) vor Profil-Default
          const aktivId = aktiveSpindelId ?? m.aktive_spindel_id;
          const verfuegbar = m._verfuegbare_spindeln ?? spindeln.filter(
            (sp) => m.spindel_ids.includes(sp.id),
          );
          return (
            <div key={m.id} className="rounded border border-gray-700 bg-camwosa-surface p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{m.name}</h3>
                  <p className="mt-1 text-sm text-camwosa-muted">
                    {m.hersteller} · {m.modell}
                  </p>
                </div>
                <button
                  className="rounded border border-gray-600 px-2 py-0.5 text-xs hover:bg-gray-700"
                  onClick={() => void exportMaschine(m.id)}
                  title="Als JSON exportieren (zum Teilen mit anderen Usern)"
                >
                  📦 Bundle
                </button>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-x-2 gap-y-1 text-xs">
                <dt className="text-camwosa-muted">{t("maschine.controller")}</dt>
                <dd>{m.controller}</dd>
                <dt className="text-camwosa-muted">{t("maschine.arbeitsraum")}</dt>
                <dd>
                  {m.arbeitsraum.x}×{m.arbeitsraum.y}×{m.arbeitsraum.z} mm
                </dd>
                <dt className="text-camwosa-muted">Vorschub</dt>
                <dd>{m.max_vorschub} mm/min</dd>
                <dt className="text-camwosa-muted">{t("maschine.modus")}</dt>
                <dd>{m.modi.join(", ")}</dd>
              </dl>

              <div className="mt-3 border-t border-gray-700 pt-2">
                <div className="mb-1 text-xs font-semibold text-camwosa-accent">
                  Spindeln ({verfuegbar.length})
                </div>
                <ul className="space-y-1 text-xs">
                  {verfuegbar.map((sp) => (
                    <li
                      key={sp.id}
                      className={
                        aktivId === sp.id
                          ? "rounded bg-camwosa-accent/20 px-2 py-1"
                          : "px-2 py-1 text-camwosa-muted"
                      }
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="min-w-0 truncate">
                          {aktivId === sp.id && "● "}
                          {sp.name}{" "}
                          <span className="text-[10px]">
                            ({HERKUNFT_LABEL[sp.herkunft]})
                          </span>
                        </span>
                        <span className="flex shrink-0 items-center gap-1">
                          <span className="text-[10px]">
                            {sp.rpm_min}–{sp.rpm_max} · {sp.typ}
                            {sp.leistung_watt ? ` · ${sp.leistung_watt}W` : ""}
                          </span>
                          {aktivId !== sp.id && (
                            <button
                              className="rounded border border-camwosa-default px-1 text-[10px] hover:text-camwosa-accent"
                              title="Als aktive Spindel setzen (für dieses Projekt)"
                              onClick={() => setAktiveSpindelId(sp.id)}
                            >
                              aktiv
                            </button>
                          )}
                          <button
                            className="rounded border border-camwosa-default px-1 text-[10px] hover:text-camwosa-text"
                            title="Spindel bearbeiten"
                            onClick={() => { setSpDetail(sp); setSpEdit("bearbeiten"); }}
                          >
                            ✏
                          </button>
                        </span>
                      </div>
                    </li>
                  ))}
                  {verfuegbar.length === 0 && (
                    <li className="px-2 py-1 italic text-camwosa-muted">
                      Keine Spindeln zugeordnet (Inline-RPM: {m.spindel_rpm_min}
                      –{m.spindel_rpm_max})
                    </li>
                  )}
                </ul>
              </div>
            </div>
          );
        })}
      </div>

      {/* Spindel-Bibliothek — alle Spindeln editierbar (Issue: alles einstellbar) */}
      <div className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="font-semibold">Spindel-Bibliothek ({spindeln.length})</h2>
          <button
            className="rounded bg-camwosa-accent px-3 py-1 text-xs font-semibold text-camwosa-bg hover:opacity-90"
            onClick={() => { setSpDetail(null); setSpEdit("neu"); }}
          >
            + Neue Spindel
          </button>
        </div>
        <table className="w-full text-xs">
          <thead className="border-b border-gray-700 text-left uppercase text-camwosa-muted">
            <tr>
              <th className="py-1">Name</th><th>Typ</th><th>Drehzahl</th>
              <th>Leistung</th><th>Hochlauf</th><th>Herkunft</th><th></th>
            </tr>
          </thead>
          <tbody>
            {spindeln.map((sp) => (
              <tr key={sp.id} className="border-b border-gray-800 hover:bg-camwosa-bg/40">
                <td className="py-1 font-medium">{sp.name}</td>
                <td>{sp.typ}</td>
                <td>{sp.rpm_min}–{sp.rpm_max}</td>
                <td>{sp.leistung_watt ? `${sp.leistung_watt} W` : "—"}</td>
                <td>{sp.rampen_zeit_s != null ? `${sp.rampen_zeit_s} s` : "—"}</td>
                <td>{HERKUNFT_LABEL[sp.herkunft]}</td>
                <td className="space-x-1 whitespace-nowrap">
                  <button className="rounded border border-gray-600 px-2 py-0.5 hover:bg-gray-700"
                    title="Bearbeiten"
                    onClick={() => { setSpDetail(sp); setSpEdit("bearbeiten"); }}>✏</button>
                  <button className="rounded border border-red-700 px-2 py-0.5 hover:bg-red-900/40"
                    title="Loeschen"
                    onClick={() => void spindelLoeschen(sp)}>🗑</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-[10px] text-camwosa-muted">
          Alle Werte (Drehzahl, VFD-Hochlauf, Spannzange …) sind hier editierbar.
          Default-Spindeln aus der Sammel-Datei lassen sich per gleichnamiger
          User-Override übersteuern.
        </p>
      </div>

      <Modal
        open={spEdit !== "none"}
        onClose={() => setSpEdit("none")}
        titel={spEdit === "neu" ? "Neue Spindel" : "Spindel bearbeiten"}
        breit
      >
        <SpindelEditor
          initial={spEdit === "bearbeiten" ? spDetail : null}
          onAbbrechen={() => setSpEdit("none")}
          onGespeichert={async () => { await reloadSpindeln(); setSpEdit("none"); }}
        />
      </Modal>
    </div>
  );
}
