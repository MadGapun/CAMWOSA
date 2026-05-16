import { useState } from "react";
import { useTranslation } from "react-i18next";
import i18n, { setzeSprache } from "../i18n";

export default function EinstellungenView() {
  const { t } = useTranslation();
  const [sprache, setSprache] = useState<"de" | "en">(
    (i18n.language as "de" | "en") || "de",
  );

  function aendereSprache(neu: "de" | "en") {
    setSprache(neu);
    setzeSprache(neu);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t("navigation.einstellungen")}</h1>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-3 font-semibold">Sprache / Language</h2>
        <div className="flex gap-2">
          <button
            className={`rounded px-4 py-2 text-sm ${
              sprache === "de"
                ? "bg-camwosa-accent text-white"
                : "bg-camwosa-bg text-camwosa-text"
            }`}
            onClick={() => aendereSprache("de")}
          >
            🇩🇪 Deutsch
          </button>
          <button
            className={`rounded px-4 py-2 text-sm ${
              sprache === "en"
                ? "bg-camwosa-accent text-white"
                : "bg-camwosa-bg text-camwosa-text"
            }`}
            onClick={() => aendereSprache("en")}
          >
            🇬🇧 English
          </button>
        </div>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-3 font-semibold">Backend</h2>
        <p className="text-sm text-camwosa-muted">
          Backend laeuft auf <code className="text-camwosa-accent">localhost</code>.
          Port wird automatisch vergeben (siehe Status-Leiste unten).
        </p>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-3 font-semibold">Verzeichnisse</h2>
        <div className="space-y-2 text-xs text-camwosa-muted">
          <div>
            <strong>Maschinen-Profile:</strong>{" "}
            <code className="text-camwosa-text">data/machines/</code>
            <br />
            <em>community/</em> fuer geteilte Profile, <em>user/</em> fuer eigene
          </div>
          <div>
            <strong>Werkzeuge:</strong>{" "}
            <code className="text-camwosa-text">data/tools/</code>
          </div>
          <div>
            <strong>Materialien:</strong>{" "}
            <code className="text-camwosa-text">data/materials/</code>
          </div>
          <div>
            <strong>Spindeln:</strong>{" "}
            <code className="text-camwosa-text">data/spindles/</code>
          </div>
          <div>
            <strong>Postprozessoren:</strong>{" "}
            <code className="text-camwosa-text">data/postprocessors/</code>
          </div>
        </div>
      </section>

      <section className="rounded border border-gray-700 bg-camwosa-surface p-4">
        <h2 className="mb-3 font-semibold">Versions-Information</h2>
        <div className="text-xs text-camwosa-muted">
          CAMWOSA v0.1.0 · Lizenz: MIT ·{" "}
          <a
            className="text-camwosa-accent hover:underline"
            href="https://github.com/MadGapun/CAMWOSA"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </div>
      </section>
    </div>
  );
}
