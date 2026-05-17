/**
 * Monaco-Syntax-Highlighter fuer CAMWOSA-G-Code.
 *
 * Erkennt:
 * - G/M-Codes
 * - Achsen-Werte (X/Y/Z/A/B/C/I/J/K)
 * - Vorschub (F), Spindel-RPM (S), Werkzeug-Nummer (T)
 * - Kommentare (`;` bis EOL)
 * - **CAMWOSA-Setup-Banner** (Zeilen ab `; DRECHSEL-JOB` oder `; ===`)
 * - **Warnungs-Zeilen** (`; WICHTIG`, `; ⚠`, `; WARNUNG`)
 * - **CNCjs-Macro-Zeilen** (`; %wait`, `; %MAKRO_NAME`)
 */

import type * as monaco from "monaco-editor";

export const SPRACHE_ID = "gcode-camwosa";
export const THEME_ID = "camwosa-dark";

/**
 * Registriert Sprache + Theme im Monaco-Singleton.
 * Idempotent — kann mehrmals aufgerufen werden.
 */
export function registriereGcodeHighlighting(m: typeof monaco) {
  if (m.languages.getLanguages().some((l) => l.id === SPRACHE_ID)) return;

  m.languages.register({ id: SPRACHE_ID, extensions: [".nc", ".gcode", ".tap"] });

  m.languages.setMonarchTokensProvider(SPRACHE_ID, {
    defaultToken: "",
    tokenPostfix: ".gcode",
    ignoreCase: true,

    tokenizer: {
      root: [
        // CAMWOSA-Setup-Banner: ganze Zeile orange
        [/^;\s*=+\s*$/, "camwosa-banner"],
        [/^;\s*DRECHSEL-JOB.*$/, "camwosa-banner"],
        [/^;\s*---\s*DRECHSELN.*$/, "camwosa-banner"],
        [/^;\s*\[.*--- Phase:.*$/, "camwosa-banner"],

        // Warnungs-Zeilen (Sicherheit)
        [/^;\s*(WICHTIG|WARNUNG|⚠).*$/i, "camwosa-warnung"],

        // CNCjs-Macro / wait
        [/^;\s*%\w+.*$/, "camwosa-macro"],

        // Normaler Kommentar
        [/;.*$/, "comment"],

        // G-Codes
        [/\bG\d+(\.\d+)?\b/i, "g-code"],
        // M-Codes
        [/\bM\d+\b/i, "m-code"],
        // Werkzeug-Nummer
        [/\bT\d+\b/i, "tool-number"],
        // Vorschub
        [/\bF[+-]?\d+(\.\d+)?\b/i, "feed"],
        // Spindel-RPM
        [/\bS\d+(\.\d+)?\b/i, "spindle"],
        // Achsen-Werte
        [/\b[XYZABCIJK][+-]?\d+(\.\d+)?\b/i, "axis"],
        // Klammer-Kommentare (manche Postprozessoren)
        [/\(.*?\)/, "comment"],
      ],
    },
  });

  // Dark-Theme — passt zu CAMWOSA-Akzentfarbe (Orange #FF6B00)
  m.editor.defineTheme(THEME_ID, {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "6B6B73", fontStyle: "italic" },
      { token: "g-code", foreground: "4A9EFF", fontStyle: "bold" },
      { token: "m-code", foreground: "FFB800", fontStyle: "bold" },
      { token: "tool-number", foreground: "B388FF", fontStyle: "bold" },
      { token: "feed", foreground: "00C26E" },
      { token: "spindle", foreground: "FF6B00", fontStyle: "bold" },
      { token: "axis", foreground: "F2F2F4" },
      { token: "camwosa-banner", foreground: "FF6B00", fontStyle: "bold" },
      { token: "camwosa-warnung", foreground: "FFB800", fontStyle: "bold" },
      { token: "camwosa-macro", foreground: "4A9EFF", fontStyle: "italic" },
    ],
    colors: {
      "editor.background": "#0A0A0B",
      "editor.foreground": "#F2F2F4",
      "editorLineNumber.foreground": "#444449",
      "editorLineNumber.activeForeground": "#FF6B00",
      "editorCursor.foreground": "#FF6B00",
      "editor.selectionBackground": "#FF6B0033",
      "editor.lineHighlightBackground": "#131316",
      "editorGutter.background": "#0A0A0B",
    },
  });
}
