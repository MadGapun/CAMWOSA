/**
 * Tailwind Config — bindet auf die CSS-Variablen aus src/styles/tokens.css.
 * Die CSS-Variablen sind themable (dark/light) + densitybar (compact/medium/comfortable)
 * und werden zur Runtime ueber data-theme / data-density am <html>-Tag umgeschaltet.
 *
 * Die alten Farb-Aliasse (camwosa.bg / .surface / .accent / .ok / .warn / .danger /
 * .text / .muted) bleiben — sie zeigen jetzt auf die CSS-Vars, damit existierende
 * Klassen nicht brechen.
 */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        camwosa: {
          bg: "var(--bg-base)",
          surface: "var(--bg-surface)",
          elevated: "var(--bg-elevated)",
          overlay: "var(--bg-overlay)",
          inset: "var(--bg-inset)",
          accent: "var(--accent)",
          "accent-hover": "var(--accent-hover)",
          "accent-soft": "var(--accent-soft)",
          warn: "var(--warning)",
          danger: "var(--danger)",
          ok: "var(--success)",
          info: "var(--info)",
          text: "var(--text-primary)",
          "text-secondary": "var(--text-secondary)",
          muted: "var(--text-muted)",
          // Override-Quelle-Farben (siehe OverrideField)
          "src-material": "var(--src-material)",
          "src-projekt": "var(--src-projekt)",
          "src-override": "var(--src-override)",
          "src-werkzeug": "var(--src-werkzeug)",
          "src-fallback": "var(--src-fallback)",
        },
      },
      borderColor: {
        camwosa: {
          subtle: "var(--border-subtle)",
          default: "var(--border-default)",
          strong: "var(--border-strong)",
        },
      },
      fontFamily: {
        sans: ["Geist", "-apple-system", "BlinkMacSystemFont", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SF Mono", "Menlo", "monospace"],
      },
      borderRadius: {
        sm: "var(--r-sm)",
        md: "var(--r-md)",
        lg: "var(--r-lg)",
        xl: "var(--r-xl)",
      },
    },
  },
  plugins: [],
};
