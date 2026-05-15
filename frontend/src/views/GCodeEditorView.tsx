import Editor from "@monaco-editor/react";
import { useTranslation } from "react-i18next";
import { useState } from "react";

const BEISPIEL = `; CAMWOSA G-Code (Beispiel)
G21
G90
G17
G94
M3 S18000
G0 X0 Y0 Z5
G1 Z-2 F400
G1 X100 Y0 F2000
G1 X100 Y50
G1 X0 Y50
G1 X0 Y0
G0 Z5
M5
M30
`;

export default function GCodeEditorView() {
  const { t } = useTranslation();
  const [value, setValue] = useState(BEISPIEL);
  return (
    <div className="space-y-2">
      <h1 className="text-xl font-bold">{t("navigation.editor")}</h1>
      <div className="overflow-hidden rounded border border-gray-700">
        <Editor
          height="70vh"
          defaultLanguage="plaintext"
          value={value}
          onChange={(v) => setValue(v ?? "")}
          theme="vs-dark"
          options={{
            minimap: { enabled: true },
            fontSize: 13,
            wordWrap: "off",
            lineNumbers: "on",
          }}
        />
      </div>
      <p className="text-xs text-camwosa-muted">
        G-Code-Mode mit Syntax-Highlighting + Befehlsbibliothek + Live-Sync folgt
        mit naechster Iteration.
      </p>
    </div>
  );
}
