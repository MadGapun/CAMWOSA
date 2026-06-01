"""Werkzeug-Anzeigename automatisch aus den Daten (Cluster D34a, Issue #33).

Markus' Anforderung: der Werkzeug-Name soll sich immer aus den Daten ergeben
(Typ + Durchmesser + Schneiden + Material + ggf. Winkel), und am Ende darf ein
optionaler eigener Zusatz (`name_zusatz`) angehängt werden.

Beispiele:
    Schaftfräser Ø6 mm · 2-Schneider · Hartmetall
    V-Bit 60° Ø12.7 mm · Hartmetall
    Kugelfräser Ø3 mm · 2-Schneider · Hartmetall (mein Liebling)
"""

from __future__ import annotations

from camwosa.db.models import Werkzeug, WerkzeugTyp

_TYP_LABEL: dict[WerkzeugTyp, str] = {
    WerkzeugTyp.SCHAFTFRAESER: "Schaftfräser",
    WerkzeugTyp.KUGELFRAESER: "Kugelfräser",
    WerkzeugTyp.TORUSFRAESER: "Torusfräser",
    WerkzeugTyp.V_BIT: "V-Bit",
    WerkzeugTyp.BALLNOSE_V_BIT: "Ballnose-V-Bit",
    WerkzeugTyp.GRAVIERSTICHEL: "Gravierstichel",
    WerkzeugTyp.BOHRER: "Bohrer",
    WerkzeugTyp.EINSCHNEIDER: "Einschneider",
    WerkzeugTyp.FISCHSCHWANZ: "Fischschwanz",
    WerkzeugTyp.SCHRUPPFRAESER: "Schruppfräser",
    WerkzeugTyp.DIAMANTGRAVIERER: "Diamantgravierer",
    WerkzeugTyp.DRAG_GRAVIERER: "Schleppgravierer",
}

# Konische Typen zeigen den Spitzenwinkel statt der Schneidenzahl prominent.
_KONISCH = {
    WerkzeugTyp.V_BIT, WerkzeugTyp.BALLNOSE_V_BIT,
    WerkzeugTyp.GRAVIERSTICHEL, WerkzeugTyp.DIAMANTGRAVIERER,
    WerkzeugTyp.DRAG_GRAVIERER,
}


def _fmt_mm(wert: float) -> str:
    """Durchmesser kompakt: 6 statt 6.0, 12.7 bleibt 12.7."""
    if abs(wert - round(wert)) < 1e-6:
        return str(int(round(wert)))
    return f"{wert:.2f}".rstrip("0").rstrip(".")


def werkzeug_auto_name(werkzeug: Werkzeug) -> str:
    """Generiert den Anzeigenamen aus den Werkzeug-Daten (ohne Zusatz)."""
    typ_label = _TYP_LABEL.get(werkzeug.typ, werkzeug.typ.value)
    teile: list[str] = [typ_label]

    if werkzeug.typ in _KONISCH and werkzeug.spitzenwinkel:
        teile.append(f"{_fmt_mm(werkzeug.spitzenwinkel)}°")

    teile.append(f"Ø{_fmt_mm(werkzeug.durchmesser)} mm")

    # Schneidenzahl (bei nicht-konischen Fräsern aussagekräftig)
    if werkzeug.typ not in _KONISCH and werkzeug.schneiden:
        teile.append(f"{werkzeug.schneiden}-Schneider")

    # Material (Hartmetall/HSS/…) — nur wenn aussagekräftig
    if werkzeug.material:
        teile.append(werkzeug.material.value)

    return " · ".join(teile)


def werkzeug_anzeigename(werkzeug: Werkzeug) -> str:
    """Voller Anzeigename: Auto-Name + optionaler eigener Zusatz."""
    basis = werkzeug_auto_name(werkzeug)
    zusatz = (werkzeug.name_zusatz or "").strip()
    if zusatz:
        return f"{basis} ({zusatz})"
    return basis


__all__ = ["werkzeug_anzeigename", "werkzeug_auto_name"]
