/**
 * Tests fuer den Varianten-Store (Master-Plan A19).
 *
 * Validiert die Snapshot-Logik: Wechsel zwischen Varianten muss die
 * Working-Stores korrekt umladen, ohne dass Daten zwischen Varianten leaken.
 */

import { beforeEach, describe, expect, it } from "vitest";
import { useAppStore } from "./store";
import { useRohmaterialStore } from "./rohmaterialStore";
import { useWorkflowStore, neueSetup } from "./workflowStore";
import { exportiereVarianten, useVarianteStore } from "./varianteStore";

function reset() {
  // Working-Stores zuruecksetzen
  useAppStore.setState({ operationen: [], aktiveOperationId: null });
  useWorkflowStore.setState({ setups: [], erledigt: {} });
  useRohmaterialStore.getState().reset();
  // Variante-Store zuruecksetzen: nur Default
  useVarianteStore.setState({
    aktiveVarianteId: "default",
    varianten: [
      {
        id: "default",
        name: "Default",
        notizen: "",
        rohmaterial: useRohmaterialStore.getState().rohmaterial,
        operationen: [],
        setups: [],
      },
    ],
  });
}

beforeEach(reset);

describe("VarianteStore Basics", () => {
  it("startet mit einer Default-Variante", () => {
    const s = useVarianteStore.getState();
    expect(s.varianten).toHaveLength(1);
    expect(s.aktiveVarianteId).toBe("default");
  });

  it("erstellen() fuegt eine neue Variante hinzu + wechselt zu ihr", () => {
    const id = useVarianteStore.getState().erstellen("Variante B");
    const s = useVarianteStore.getState();
    expect(s.varianten).toHaveLength(2);
    expect(s.aktiveVarianteId).toBe(id);
    expect(s.varianten.find((v) => v.id === id)?.name).toBe("Variante B");
  });

  it("umbenennen() aendert nur den Namen", () => {
    useVarianteStore.getState().umbenennen("default", "Strategie A");
    expect(useVarianteStore.getState().varianten[0].name).toBe("Strategie A");
  });

  it("notizenSetzen() aktualisiert die Notizen", () => {
    useVarianteStore.getState().notizenSetzen("default", "Erste Strategie");
    expect(useVarianteStore.getState().varianten[0].notizen).toBe("Erste Strategie");
  });

  it("loeschen() der letzten Variante ist no-op", () => {
    useVarianteStore.getState().loeschen("default");
    expect(useVarianteStore.getState().varianten).toHaveLength(1);
  });
});

describe("Snapshot-Logik beim Wechsel", () => {
  it("schreibt aktuelle Operationen vor dem Wechsel in die alte Variante", () => {
    // Default-Variante mit einer Operation befuellen
    useAppStore.setState({
      operationen: [{ id: "op1", name: "Test-Op", typ: "kontur" } as never],
    });
    // Neue Variante anlegen (intern wird default-Snapshot gesichert)
    const idB = useVarianteStore.getState().erstellen("B");
    // Working-Store muss nach Wechsel leer sein (B ist leer)
    expect(useAppStore.getState().operationen).toHaveLength(0);
    // Default-Variante hat die alte Operation behalten
    const def = useVarianteStore
      .getState()
      .varianten.find((v) => v.id === "default")!;
    expect(def.operationen).toHaveLength(1);
    expect(def.operationen[0].id).toBe("op1");
    // Zurueck zu Default -> Operation ist wieder da
    useVarianteStore.getState().wechseln("default");
    expect(useAppStore.getState().operationen).toHaveLength(1);
    expect(useAppStore.getState().operationen[0].id).toBe("op1");
    // Aktive Variante ist wieder default
    expect(useVarianteStore.getState().aktiveVarianteId).toBe("default");
    expect(idB).not.toBe("default");
  });

  it("setups werden mit der aktiven Variante mitgewechselt", () => {
    useWorkflowStore.getState().hinzufuegen(neueSetup("Setup A", "werkzeug_1"));
    const idB = useVarianteStore.getState().erstellen("B");
    expect(useWorkflowStore.getState().setups).toHaveLength(0);
    useVarianteStore.getState().wechseln("default");
    expect(useWorkflowStore.getState().setups).toHaveLength(1);
    useVarianteStore.getState().wechseln(idB);
    expect(useWorkflowStore.getState().setups).toHaveLength(0);
  });

  it("rohmaterial-Aenderung leakt nicht zwischen Varianten", () => {
    useRohmaterialStore.getState().setze({ laenge: 555 });
    useVarianteStore.getState().erstellen("B"); // wechselt nach B
    useRohmaterialStore.getState().setze({ laenge: 999 });
    // Default-Variante muss noch 555 haben
    useVarianteStore.getState().wechseln("default");
    expect(useRohmaterialStore.getState().rohmaterial.laenge).toBe(555);
  });

  it("Wechsel auf bereits aktive Variante ist no-op", () => {
    useAppStore.setState({
      operationen: [{ id: "op1", name: "X", typ: "kontur" } as never],
    });
    useVarianteStore.getState().wechseln("default");
    expect(useAppStore.getState().operationen).toHaveLength(1);
  });
});

describe("Duplizieren", () => {
  it("erstellen() mit dupliziereVon uebernimmt Operationen mit neuen IDs", () => {
    useAppStore.setState({
      operationen: [
        { id: "op1", name: "A", typ: "kontur" } as never,
        { id: "op2", name: "B", typ: "tasche" } as never,
      ],
    });
    const idDupl = useVarianteStore.getState().erstellen("Kopie", "default");
    const kopie = useVarianteStore.getState().varianten.find((v) => v.id === idDupl)!;
    expect(kopie.operationen).toHaveLength(2);
    // Neue IDs!
    expect(kopie.operationen[0].id).not.toBe("op1");
    expect(kopie.operationen[1].id).not.toBe("op2");
    expect(kopie.operationen[0].name).toBe("A");
    // Working-Store hat jetzt die Kopie (mit neuen IDs)
    expect(useAppStore.getState().operationen[0].id).not.toBe("op1");
  });

  it("Duplizieren erbt Rohmaterial-Werte als Kopie", () => {
    useRohmaterialStore.getState().setze({ laenge: 321 });
    const idDupl = useVarianteStore.getState().erstellen("Klon", "default");
    const klon = useVarianteStore.getState().varianten.find((v) => v.id === idDupl)!;
    expect(klon.rohmaterial.laenge).toBe(321);
    // Aenderung im Klon darf die Quelle nicht treffen
    useRohmaterialStore.getState().setze({ laenge: 654 });
    useVarianteStore.getState().wechseln("default");
    expect(useRohmaterialStore.getState().rohmaterial.laenge).toBe(321);
  });
});

describe("Loeschen", () => {
  it("Loeschen der aktiven Variante wechselt auf die erste verbleibende", () => {
    const idB = useVarianteStore.getState().erstellen("B");
    useVarianteStore.getState().loeschen(idB);
    const s = useVarianteStore.getState();
    expect(s.varianten).toHaveLength(1);
    expect(s.aktiveVarianteId).toBe("default");
  });

  it("Loeschen einer nicht-aktiven Variante laesst Aktive unangetastet", () => {
    const idB = useVarianteStore.getState().erstellen("B");
    useVarianteStore.getState().wechseln("default");
    useVarianteStore.getState().loeschen(idB);
    expect(useVarianteStore.getState().aktiveVarianteId).toBe("default");
    expect(useVarianteStore.getState().varianten).toHaveLength(1);
  });
});

describe("init() und Export", () => {
  it("init() ersetzt die Liste und laedt die Default-Variante", () => {
    useVarianteStore.getState().init(
      [
        {
          id: "v1",
          name: "Strategie 1",
          notizen: "",
          rohmaterial: useRohmaterialStore.getState().rohmaterial,
          operationen: [{ id: "x", name: "X", typ: "kontur" } as never],
          setups: [],
        },
      ],
      "v1",
    );
    expect(useVarianteStore.getState().varianten).toHaveLength(1);
    expect(useVarianteStore.getState().aktiveVarianteId).toBe("v1");
    expect(useAppStore.getState().operationen).toHaveLength(1);
  });

  it("init() mit leerer Liste behaelt Default-Variante", () => {
    useVarianteStore.getState().init([], null);
    expect(useVarianteStore.getState().varianten).toHaveLength(1);
    expect(useVarianteStore.getState().varianten[0].id).toBe("default");
  });

  it("exportiereVarianten() liefert alle Varianten + aktive id", () => {
    useVarianteStore.getState().erstellen("Zweite");
    const out = exportiereVarianten();
    expect(out.varianten).toHaveLength(2);
    expect(out.aktive_variante).toBeTruthy();
    expect(out.varianten.every((v) => "rohmaterial" in v && "setups" in v)).toBe(true);
  });
});
