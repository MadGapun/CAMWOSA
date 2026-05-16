import { ReactNode } from "react";

interface Props {
  open: boolean;
  titel: string;
  onClose: () => void;
  children: ReactNode;
  breit?: boolean;
}

export default function Modal({ open, titel, onClose, children, breit }: Props) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className={`max-h-[90vh] overflow-auto rounded-lg border border-gray-700 bg-camwosa-surface shadow-xl ${
          breit ? "w-[900px]" : "w-[500px]"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-gray-700 px-4 py-3">
          <h2 className="text-base font-semibold">{titel}</h2>
          <button
            className="rounded px-2 py-1 text-camwosa-muted hover:bg-gray-700 hover:text-white"
            onClick={onClose}
            aria-label="Schliessen"
          >
            ×
          </button>
        </header>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
