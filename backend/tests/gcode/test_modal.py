"""Tests fuer die modale G-code-Kompression (Cluster P2, Issue #54)."""

from __future__ import annotations

from camwosa.gcode.modal import komprimiere_modal


def _resolve(zeilen: list[str]) -> list[tuple]:
    """Spielt den modalen Zustand nach → Liste (motion,x,y,z,f) je Bewegungszeile.

    Damit lässt sich Endpunkt-Treue pruefen: komprimierter G-code muss dieselbe
    Bahn beschreiben wie das Original.
    """
    motion = None
    x = y = z = f = None
    aus: list[tuple] = []
    for zeile in zeilen:
        code = zeile.split(";", 1)[0].strip()
        if not code:
            continue
        worte = code.split()
        cmd = worte[0].upper()
        if cmd in ("G0", "G1", "G2", "G3"):
            motion = cmd
            rest = worte[1:]
        elif cmd[0] in ("X", "Y", "Z", "I", "J", "F"):
            rest = worte  # Bewegungs-Wort modal weggelassen
        else:
            motion = None  # Nicht-Bewegung
            continue
        for w in rest:
            ltr, val = w[0].upper(), w[1:]
            if ltr == "X":
                x = float(val)
            elif ltr == "Y":
                y = float(val)
            elif ltr == "Z":
                z = float(val)
            elif ltr == "F":
                f = float(val)
        if motion in ("G0", "G1", "G2", "G3"):
            aus.append((motion, x, y, z, f))
    return aus


BEISPIEL = [
    "; Operation: Tasche",
    "M3 S18000",
    "G0 X10.000 Y10.000 Z5.000",
    "G1 X10.000 Y10.000 Z-1.000 F300",
    "G1 X50.000 Y10.000 Z-1.000 F800",
    "G1 X50.000 Y40.000 Z-1.000 F800",
    "G1 X10.000 Y40.000 Z-1.000 F800",
    "G0 X10.000 Y40.000 Z5.000",
    "M5",
]


class TestEndpunktTreue:
    def test_bahn_bleibt_identisch(self):
        komp = komprimiere_modal(BEISPIEL)
        assert _resolve(komp) == _resolve(BEISPIEL)

    def test_arc_bahn_bleibt_identisch(self):
        arc = [
            "G1 X0.000 Y0.000 Z-1.000 F600",
            "G2 X10.000 Y10.000 Z-1.000 I10.000 J0.000 F600",
            "G2 X20.000 Y0.000 Z-1.000 I0.000 J-10.000 F600",
        ]
        assert _resolve(komprimiere_modal(arc)) == _resolve(arc)


class TestKompression:
    def test_feed_nur_bei_aenderung(self):
        komp = komprimiere_modal(BEISPIEL)
        # F300 einmal, F800 einmal — nicht auf jeder Zeile
        assert sum(z.count("F300") for z in komp) == 1
        assert sum(z.count("F800") for z in komp) == 1

    def test_unveraenderte_achse_entfaellt(self):
        komp = komprimiere_modal(BEISPIEL)
        # reiner X-Zug darf kein Y/Z mehr tragen
        x_zug = [z for z in komp if z.startswith("X50.000")][0]
        assert "Y" not in x_zug
        assert "Z" not in x_zug

    def test_bewegungswort_wird_modal(self):
        komp = komprimiere_modal(BEISPIEL)
        # nach dem ersten G1 folgen Zeilen ohne erneutes "G1 "
        assert any(z.startswith("X") or z.startswith("Y") for z in komp)

    def test_kompakter_als_original(self):
        komp = komprimiere_modal(BEISPIEL)
        laenge_orig = sum(len(z) for z in BEISPIEL)
        laenge_komp = sum(len(z) for z in komp)
        assert laenge_komp < laenge_orig

    def test_arc_behaelt_ij(self):
        arc = ["G2 X10.000 Y10.000 Z-1.000 I10.000 J0.000 F600"]
        komp = komprimiere_modal(arc)
        assert "I10.000" in komp[0] and "J0.000" in komp[0]


class TestRobustheit:
    def test_kommentare_bleiben(self):
        komp = komprimiere_modal(BEISPIEL)
        assert any("Operation: Tasche" in z for z in komp)

    def test_nichtbewegung_durchgereicht(self):
        komp = komprimiere_modal(BEISPIEL)
        assert "M3 S18000" in komp
        assert "M5" in komp

    def test_leere_eingabe(self):
        assert komprimiere_modal([]) == []

    def test_motion_wort_nach_nichtbewegung_wieder_da(self):
        zeilen = [
            "G1 X0.000 Y0.000 Z-1.000 F600",
            "G1 X10.000 Y0.000 Z-1.000 F600",
            "M5",
            "G1 X20.000 Y0.000 Z-1.000 F600",
        ]
        komp = komprimiere_modal(zeilen)
        # nach M5 muss die naechste Bewegung wieder G1 nennen
        idx = komp.index("M5")
        assert komp[idx + 1].startswith("G1")
