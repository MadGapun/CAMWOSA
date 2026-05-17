import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../state/store";
import { camwosaApi } from "../api/client";
import Modal from "../components/Modal";
import MaterialEditor from "../editor/MaterialEditor";
import CuttingPresetEditor from "../editor/CuttingPresetEditor";
import type { Material } from "../api/types";

export default function MaterialienView() {
  const { t } = useTranslation();
  const materialien = useAppStore((s) => s.materialien);
  const setMaterialien = useAppStore((s) => s.setMaterialien);
  const werkzeuge = useAppStore((s) => s.werkzeuge);
  const [editMode, setEditMode] = useState<"none" | "neu" | "bearbeiten">("none");
  const [detailId, setDetailId] = useState<string | null>(null);

  const detail = materialien.find((m) => m.id === detailId) ?? null;

  async function reload() {
    setMaterialien(await camwosaApi.materialien());
  }

  async function loeschen(m: Material) {
    if (!window.confirm(`Material '${m.name}' loeschen?`)) return;
    try {
      await camwosaApi.materialLoeschen(m.id);
      await reload();
    } catch (e: any) {
      window.alert(`Loeschen fehlgeschlagen: ${e.response?.data?.fehler ?? e.message}`);
    }
  }

  const grouped = materialien.reduce<Record<string, typeof materialien>>((acc, m) => {
    (acc[m.kategorie] ??= []).push(m);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">{t("navigation.materialien")}</h1>
        <button
          className="rounded bg-camwosa-accent px-3 py-1 text-sm font-medium text-camwosa-bg hover:opacity-90"
          onClick={() => { setDetailId(null); setEditMode("neu"); }}
        >
          + Neues Material
        </button>
      </div>

      {Object.entries(grouped).map(([kat, items]) => (
        <section key={kat}>
          <h2 className="mb-2 font-semibold capitalize">{kat}</h2>
          <ul className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {items.map((m) => (
              <li key={m.id}
                className="cursor-pointer rounded border border-gray-700 bg-camwosa-surface p-3 hover:border-camwosa-accent"
                onClick={() => setDetailId(m.id)}
              >
                <div className="font-medium">{m.name}</div>
                <div className="text-xs text-camwosa-muted">{m.unter_kategorie}</div>
                {m.janka_haerte != null && (
                  <div className="mt-1 text-xs">Janka: {m.janka_haerte}</div>
                )}
                <div className="mt-1 text-xs text-camwosa-muted">
                  {m.presets.length} Legacy-Presets
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <Modal
        open={detail !== null}
        onClose={() => setDetailId(null)}
        titel={detail ? `Material: ${detail.name}` : ""}
        breit
      >
        {detail && (
          <div className="space-y-4">
            <div className="flex gap-2">
              <button
                className="rounded border border-gray-600 px-3 py-1 text-xs hover:bg-gray-700"
                onClick={() => setEditMode("bearbeiten")}
              >
                ✏ Bearbeiten
              </button>
              <button
                className="rounded border border-red-700 px-3 py-1 text-xs hover:bg-red-900/40"
                onClick={() => void loeschen(detail)}
              >
                🗑 Loeschen
              </button>
            </div>
            <CuttingPresetEditor material={detail} werkzeuge={werkzeuge} />
          </div>
        )}
      </Modal>

      <Modal
        open={editMode !== "none"}
        onClose={() => setEditMode("none")}
        titel={editMode === "neu" ? "Neues Material" : "Material bearbeiten"}
        breit
      >
        <MaterialEditor
          initial={editMode === "bearbeiten" ? detail : null}
          onAbbrechen={() => setEditMode("none")}
          onGespeichert={async () => {
            await reload();
            setEditMode("none");
          }}
        />
      </Modal>
    </div>
  );
}
