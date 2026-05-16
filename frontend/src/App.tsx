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
import ZeichnenView from "./views/ZeichnenView";
import GCodeEditorView from "./views/GCodeEditorView";
import WorkflowView from "./views/WorkflowView";
import NestingView from "./views/NestingView";
import EinstellungenView from "./views/EinstellungenView";

export default function App() {
  return (
    <div className="flex h-screen w-screen flex-col">
      <Topbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto bg-camwosa-bg p-4">
          <Routes>
            <Route path="/" element={<Navigate to="/projekt" replace />} />
            <Route path="/projekt" element={<ProjektView />} />
            <Route path="/maschinen" element={<MaschinenView />} />
            <Route path="/werkzeuge" element={<WerkzeugeView />} />
            <Route path="/materialien" element={<MaterialienView />} />
            <Route path="/zeichnen" element={<ZeichnenView />} />
            <Route path="/operationen" element={<OperationenView />} />
            <Route path="/preview" element={<PreviewView />} />
            <Route path="/editor" element={<GCodeEditorView />} />
            <Route path="/workflow" element={<WorkflowView />} />
            <Route path="/nesting" element={<NestingView />} />
            <Route path="/einstellungen" element={<EinstellungenView />} />
          </Routes>
        </main>
      </div>
      <StatusBar />
    </div>
  );
}
