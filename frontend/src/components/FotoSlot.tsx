/**
 * Foto-Slot fuer Setups.
 *
 * Pro Setup kann ein Bild abgelegt werden (Aufspannung dokumentieren).
 * Speicherung: data-URL im Setup-Objekt (foto_pfad) — beim .cwp-Export wird
 * das eingebettet (Phase 1+ — aktuell nur im State).
 */

import { useRef } from "react";

interface Props {
  fotoPfad: string | null;
  onChange: (dataUrl: string | null) => void;
}

export default function FotoSlot({ fotoPfad, onChange }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  function onFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result === "string") onChange(result);
    };
    reader.readAsDataURL(file);
  }

  return (
    <div className="rounded border border-gray-700 bg-camwosa-bg p-2">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs text-camwosa-muted">Setup-Foto</span>
        <div className="flex gap-1">
          <button
            className="rounded border border-gray-600 px-2 py-0.5 text-[10px] hover:bg-gray-700"
            onClick={() => fileRef.current?.click()}
          >
            {fotoPfad ? "Aendern" : "+ Foto"}
          </button>
          {fotoPfad && (
            <button
              className="rounded border border-gray-600 px-2 py-0.5 text-[10px] text-camwosa-muted hover:text-camwosa-danger"
              onClick={() => onChange(null)}
            >
              Entfernen
            </button>
          )}
        </div>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
        }}
      />
      {fotoPfad ? (
        <img
          src={fotoPfad}
          alt="Setup-Foto"
          className="max-h-48 w-full rounded object-contain"
        />
      ) : (
        <div className="flex h-24 items-center justify-center text-xs text-camwosa-muted">
          (kein Foto)
        </div>
      )}
    </div>
  );
}
