import { useEffect, useState } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatusBar from "./components/StatusBar";
import ProjektView from "./views/ProjektView";
import MaschinenView from "./views/MaschinenView";
import WerkzeugeView from "./views/WerkzeugeView";
import MaterialienView from "./views/MaterialienView";
import OperationenView from "./views/OperationenView";
import PreviewView from "./views/PreviewView";
import Simulation3DView from "./views/Simulation3DView";
import ZeichnenView from "./views/ZeichnenView";
import GCodeEditorView from "./views/GCodeEditorView";
import WorkflowView from "./views/WorkflowView";
import NestingView from "./views/NestingView";
import EinstellungenView from "./views/EinstellungenView";
import QuickStartView from "./views/QuickStartView";
import DrechselnView from "./views/DrechselnView";
import WrapView from "./views/WrapView";
import MaterialAbtragView from "./views/MaterialAbtragView";
import BildReliefView from "./views/BildReliefView";
import { useUIPrefs } from "./state/uiPrefs";
import FirstRunWizard, { firstRunErledigt } from "./components/FirstRunWizard";

export default function App() {
  const [wizardOffen, setWizardOffen] = useState(() => !firstRunErledigt());
  const sidebarSichtbar = useUIPrefs((s) => s.sidebarSichtbar);
  const topbarSichtbar = useUIPrefs((s) => s.topbarSichtbar);
  const statusbarSichtbar = useUIPrefs((s) => s.statusbarSichtbar);
  const fokus = useUIPrefs((s) => s.fokusModus);
  const toggleFokus = useUIPrefs((s) => s.toggleFokus);
  const setSidebar = useUIPrefs((s) => s.setSidebarSichtbar);
  const setTopbar = useUIPrefs((s) => s.setTopbarSichtbar);
  const setStatusbar = useUIPrefs((s) => s.setStatusbarSichtbar);

  // Im Fokus-Modus alle Chrome-Leisten unsichtbar machen — unabhaengig der
  // persistenten Einzel-Einstellungen.
  const showSidebar = sidebarSichtbar && !fokus;
  const showTopbar = topbarSichtbar && !fokus;
  const showStatusbar = statusbarSichtbar && !fokus;

  // Hotkeys: F = Fokus an/aus · Esc verlaesst Fokus · b = Sidebar · t = Topbar
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Wenn der User gerade in ein Input/Textarea tippt — Hotkeys nicht greifen
      const tag = (e.target as HTMLElement | null)?.tagName ?? "";
      const istEingabe =
        tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT"
        || (e.target as HTMLElement | null)?.isContentEditable;
      if (istEingabe) return;
      // Modifier raus, sonst kollidiert mit Browser-Shortcuts
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      if (e.key === "f" || e.key === "F") {
        e.preventDefault();
        toggleFokus();
      } else if (e.key === "Escape" && fokus) {
        e.preventDefault();
        toggleFokus();
      } else if (e.key === "b" || e.key === "B") {
        e.preventDefault();
        setSidebar(!sidebarSichtbar);
      } else if (e.key === "t" || e.key === "T") {
        e.preventDefault();
        setTopbar(!topbarSichtbar);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [fokus, toggleFokus, sidebarSichtbar, topbarSichtbar, setSidebar, setTopbar]);

  return (
    <div className="flex h-screen w-screen flex-col">
      {showTopbar && <Topbar />}
      <div className="flex flex-1 overflow-hidden">
        {showSidebar && <Sidebar />}
        <main className="relative flex-1 overflow-auto bg-camwosa-bg p-4">
          <Routes>
            <Route path="/" element={<Navigate to="/quickstart" replace />} />
            <Route path="/quickstart" element={<QuickStartView />} />
            <Route path="/projekt" element={<ProjektView />} />
            <Route path="/maschinen" element={<MaschinenView />} />
            <Route path="/werkzeuge" element={<WerkzeugeView />} />
            <Route path="/materialien" element={<MaterialienView />} />
            <Route path="/zeichnen" element={<ZeichnenView />} />
            <Route path="/operationen" element={<OperationenView />} />
            <Route path="/preview" element={<PreviewView />} />
            <Route path="/simulation" element={<Simulation3DView />} />
            <Route path="/editor" element={<GCodeEditorView />} />
            <Route path="/workflow" element={<WorkflowView />} />
            <Route path="/drechseln" element={<DrechselnView />} />
            <Route path="/wrap" element={<WrapView />} />
            <Route path="/abtrag" element={<MaterialAbtragView />} />
            <Route path="/bild-relief" element={<BildReliefView />} />
            <Route path="/nesting" element={<NestingView />} />
            <Route path="/einstellungen" element={<EinstellungenView />} />
          </Routes>

          {/* Floating-Toggles: immer sichtbar, damit man aus Fokus-Modus wieder rauskommt */}
          <ChromeToggleBar
            sidebar={sidebarSichtbar}
            topbar={topbarSichtbar}
            statusbar={statusbarSichtbar}
            fokus={fokus}
            onToggleSidebar={() => setSidebar(!sidebarSichtbar)}
            onToggleTopbar={() => setTopbar(!topbarSichtbar)}
            onToggleStatusbar={() => setStatusbar(!statusbarSichtbar)}
            onToggleFokus={toggleFokus}
          />
        </main>
      </div>
      {showStatusbar && <StatusBar />}
      {wizardOffen && <FirstRunWizard onClose={() => setWizardOffen(false)} />}
    </div>
  );
}

/**
 * Schwebende Mini-Toolbar oben rechts — vier Toggles fuer die Chrome-Leisten.
 * Bewusst klein (32px) und semi-transparent, damit sie nicht stoert wenn alles
 * sichtbar ist. Im Fokus-Modus ist sie der einzige Weg zurueck (neben Esc/F).
 */
function ChromeToggleBar({
  sidebar, topbar, statusbar, fokus,
  onToggleSidebar, onToggleTopbar, onToggleStatusbar, onToggleFokus,
}: {
  sidebar: boolean;
  topbar: boolean;
  statusbar: boolean;
  fokus: boolean;
  onToggleSidebar: () => void;
  onToggleTopbar: () => void;
  onToggleStatusbar: () => void;
  onToggleFokus: () => void;
}) {
  return (
    // #51: container faengt keine Klicks ab (pointer-events-none); nur die
    // Buttons selbst. Im Normalfall ist nur der Fokus-Button sichtbar (kleine
    // Klick-Flaeche in der Ecke), die drei Chrome-Toggles klappen erst beim
    // Hover nach links auf — so liegt nichts Klickbares ueber den View-Buttons.
    <div className="group pointer-events-none absolute right-2 top-2 z-50 flex items-start gap-1">
      <div className="hidden gap-1 opacity-30 transition-opacity group-hover:flex group-hover:opacity-100">
        <Btn
          title={`Sidebar ${sidebar ? "ausblenden" : "einblenden"} (B)`}
          aktiv={sidebar}
          onClick={onToggleSidebar}
        >
          ▤
        </Btn>
        <Btn
          title={`Topbar ${topbar ? "ausblenden" : "einblenden"} (T)`}
          aktiv={topbar}
          onClick={onToggleTopbar}
        >
          ▔
        </Btn>
        <Btn
          title={`Statusbar ${statusbar ? "ausblenden" : "einblenden"}`}
          aktiv={statusbar}
          onClick={onToggleStatusbar}
        >
          ▁
        </Btn>
      </div>
      <Btn
        title={fokus ? "Fokus verlassen (F oder Esc)" : "Fokus-Modus: alle Leisten aus (F) — hover fuer mehr"}
        aktiv={fokus}
        onClick={onToggleFokus}
      >
        {fokus ? "◰" : "▣"}
      </Btn>
    </div>
  );
}

function Btn({
  title, aktiv, onClick, children,
}: {
  title: string; aktiv: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      className={[
        "pointer-events-auto rounded border px-2 py-1 text-xs backdrop-blur",
        aktiv
          ? "border-camwosa-accent/40 bg-camwosa-accent-soft text-camwosa-accent"
          : "border-camwosa-default bg-camwosa-surface/80 text-camwosa-muted hover:text-camwosa-text",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
