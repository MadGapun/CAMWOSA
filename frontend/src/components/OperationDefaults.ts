import type {
  BohrParameter,
  GravurParameter,
  KonturParameter,
  OperationsTyp,
  TaschenParameter,
} from "../api/types";

export function defaultsFuer(typ: OperationsTyp, werkzeug_id: string): unknown {
  const basis = {
    werkzeug_id,
    spindel_rpm: 18000,
    vorschub: 2000,
    eintauch_vorschub: 400,
    sicherheitshoehe: 5,
    max_tiefe: 6,
    stepdown: 2,
  };
  switch (typ) {
    case "kontur":
      return {
        ...basis,
        seite: "aussen",
        fraes_richtung: "gleichlauf",
        eintauch_strategie: "rampe",
        rampe_winkel_grad: 15,
        tabs_anzahl: 0,
        tabs_hoehe: 1.5,
        tabs_breite: 4,
        aufmass: 0,
        schlichtgang: false,
        lead_in_laenge: 0,
        lead_out_laenge: 0,
      } satisfies KonturParameter;
    case "tasche":
      return {
        ...basis,
        max_tiefe: 4,
        strategie: "parallel",
        stepover_prozent: 40,
        eintauch_strategie: "helix",
        rampe_winkel_grad: 15,
        aufmass_wand: 0,
        aufmass_boden: 0,
        schlichtgang_wand: false,
        schlichtgang_boden: false,
        fraes_richtung: "gleichlauf",
      } satisfies TaschenParameter;
    case "bohren":
      return {
        ...basis,
        spindel_rpm: 15000,
        vorschub: 500,
        eintauch_vorschub: 300,
        max_tiefe: 10,
        stepdown: 10,
        strategie: "peck",
        peck_tiefe: 2,
        dwell_sekunden: 0,
        rueckzugs_hoehe: 2,
      } satisfies BohrParameter;
    case "gravur":
      return {
        ...basis,
        spindel_rpm: 18000,
        vorschub: 1500,
        max_tiefe: 1,
        stepdown: 0.5,
        strategie: "konstante_tiefe",
        spitzenwinkel_grad: null,
        max_zustellung: 0.5,
      } satisfies GravurParameter;
  }
  throw new Error(`Unbekannter Operations-Typ: ${typ}`);
}
