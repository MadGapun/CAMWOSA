"""Modale G-code-Kompression (Cluster P2, Issue #54).

GRBL ist **modal**: Achsworte (X/Y/Z), der Vorschub (F) und das Bewegungs-Wort
(G0/G1/G2/G3) gelten weiter, bis sie geaendert werden. Der CAMWOSA-Postprozessor
schreibt sie aber auf *jeder* Zeile neu — das blaeht die Datei auf (2-3x) und
setzt Z auf reinen XY-Zuegen erneut (Mikro-Jitter durch Rundung).

``komprimiere_modal`` ist ein **endpunkt-treuer Post-Pass** auf den fertigen
G-code-Zeilen: er entfernt redundante Achsworte, wiederholten Vorschub und
wiederholtes Bewegungs-Wort, ohne die gefahrene Bahn zu veraendern.

Konservativ:
- Boegen (G2/G3) behalten **immer** X, Y, I, J (Bogen-Semantik) — nur F wird komprimiert.
- Nach jeder Nicht-Bewegungszeile (M3, G4, G54, …) wird das Bewegungs-Wort
  wieder voll ausgegeben (kein Verlass auf Modal-Zustand ueber Sonderzeilen).
- Reine Kommentarzeilen bleiben unangetastet und aendern den Zustand nicht.
- Wird eine Bewegungszeile zur No-Op (gleiche Position, kein neuer Wert), faellt
  sie weg (bzw. bleibt als Kommentar erhalten, falls sie einen trug).
"""

from __future__ import annotations

_EPS = 1e-6
_MOTION = {"G0", "G1", "G00", "G01", "G2", "G3", "G02", "G03"}
_LINEAR = {"G0", "G1", "G00", "G01"}


def _split_kommentar(zeile: str) -> tuple[str, str]:
    """Trennt Code-Teil und Kommentar (';' …). Kommentar inkl. ';'."""
    idx = zeile.find(";")
    if idx == -1:
        return zeile.rstrip(), ""
    return zeile[:idx].rstrip(), zeile[idx:].rstrip()


def komprimiere_modal(zeilen: list[str]) -> list[str]:
    """Entfernt redundante modale Worte aus GRBL-G-code. Bahn bleibt identisch."""
    out: list[str] = []
    last_motion: str | None = None
    last: dict[str, float] = {}  # X/Y/Z/F -> zuletzt gesetzter Wert

    for zeile in zeilen:
        code, kommentar = _split_kommentar(zeile)
        if not code:
            # reine Kommentar- oder Leerzeile: unveraendert, kein Zustandswechsel
            out.append(zeile)
            continue

        worte = code.split()
        cmd = worte[0].upper()

        if cmd not in _MOTION:
            # Nicht-Bewegung (M3, G4, G21, G54, …): unveraendert durchreichen.
            # Modal-Bewegungswort zuruecksetzen → naechste Bewegung nennt es wieder.
            out.append(zeile)
            last_motion = None
            continue

        # --- Bewegungszeile: Worte parsen --------------------------------
        achsen: dict[str, str] = {}  # Buchstabe -> Original-Token (z.B. "X10.000")
        werte: dict[str, float] = {}
        for w in worte[1:]:
            letter = w[0].upper()
            try:
                werte[letter] = float(w[1:])
            except (ValueError, IndexError):
                werte[letter] = float("nan")
            achsen[letter] = w

        ist_bogen = cmd in ("G2", "G3", "G02", "G03")
        teile: list[str] = []

        # Bewegungs-Wort nur bei Wechsel
        if cmd != last_motion:
            teile.append(worte[0])
            last_motion = cmd

        # Achsworte
        for ax in ("X", "Y", "Z"):
            if ax not in achsen:
                continue
            v = werte[ax]
            geaendert = ax not in last or abs(v - last[ax]) > _EPS
            # Bei Boegen X/Y immer behalten (Endpunkt-Pflicht)
            if geaendert or (ist_bogen and ax in ("X", "Y")):
                teile.append(achsen[ax])
            last[ax] = v

        # Bogen-Zentrum I/J immer behalten
        for ax in ("I", "J"):
            if ax in achsen:
                teile.append(achsen[ax])

        # Vorschub nur bei Wechsel (G0 hat keinen)
        if "F" in achsen and not cmd.startswith("G0"):
            v = werte["F"]
            if "F" not in last or abs(v - last["F"]) > _EPS:
                teile.append(achsen["F"])
            last["F"] = v
        elif "F" in achsen:
            # G0 mit F (untypisch) — F merken, aber nicht ausgeben
            last["F"] = werte["F"]

        if not teile:
            # No-Op (gleiche Position, kein neuer Wert)
            if kommentar:
                out.append(kommentar)
            continue

        rebuilt = " ".join(teile)
        if kommentar:
            rebuilt += f"  {kommentar}"
        out.append(rebuilt)

    return out


__all__ = ["komprimiere_modal"]
