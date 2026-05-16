import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import de from "./locales/de.json";
import en from "./locales/en.json";

const SPRACH_KEY = "camwosa.sprache";

const gespeichert = typeof window !== "undefined"
  ? window.localStorage?.getItem(SPRACH_KEY)
  : null;

void i18n.use(initReactI18next).init({
  resources: {
    de: { translation: de },
    en: { translation: en },
  },
  lng: gespeichert ?? "de",
  fallbackLng: "de",
  interpolation: { escapeValue: false },
});

export function setzeSprache(sprache: "de" | "en"): void {
  void i18n.changeLanguage(sprache);
  if (typeof window !== "undefined") {
    window.localStorage?.setItem(SPRACH_KEY, sprache);
  }
}

export default i18n;
