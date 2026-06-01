"""Tests fuer Werkzeug-Auto-Name (D34a)."""

from __future__ import annotations

from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.db.werkzeug_name import werkzeug_anzeigename, werkzeug_auto_name


def _wz(**kw):
    d = dict(id="t", name="", typ=WerkzeugTyp.SCHAFTFRAESER, durchmesser=6,
             schaft_durchmesser=6, schneidlaenge=12, gesamtlaenge=40, schneiden=2)
    d.update(kw)
    return Werkzeug(**d)


class TestAutoName:
    def test_schaftfraeser(self):
        name = werkzeug_auto_name(_wz(durchmesser=6, schneiden=2))
        assert "Schaftfräser" in name
        assert "Ø6 mm" in name
        assert "2-Schneider" in name

    def test_durchmesser_komma(self):
        name = werkzeug_auto_name(_wz(durchmesser=12.7))
        assert "Ø12.7 mm" in name

    def test_durchmesser_ganzzahl_ohne_komma(self):
        name = werkzeug_auto_name(_wz(durchmesser=3.0))
        assert "Ø3 mm" in name
        assert "3.0" not in name

    def test_vbit_zeigt_winkel_nicht_schneiden(self):
        name = werkzeug_auto_name(_wz(
            typ=WerkzeugTyp.V_BIT, durchmesser=12.7, spitzenwinkel=60,
        ))
        assert "V-Bit" in name
        assert "60°" in name
        assert "Schneider" not in name  # konisch → keine Schneidenzahl

    def test_material_im_namen(self):
        from camwosa.db.models import WerkzeugMaterial
        name = werkzeug_auto_name(_wz(material=WerkzeugMaterial.HSS))
        assert "HSS" in name


class TestAnzeigename:
    def test_ohne_zusatz_gleich_autoname(self):
        wz = _wz()
        assert werkzeug_anzeigename(wz) == werkzeug_auto_name(wz)

    def test_mit_zusatz_angehaengt(self):
        wz = _wz(name_zusatz="mein Liebling")
        name = werkzeug_anzeigename(wz)
        assert name.endswith("(mein Liebling)")
        assert werkzeug_auto_name(wz) in name

    def test_leerer_zusatz_ignoriert(self):
        wz = _wz(name_zusatz="   ")
        assert "(" not in werkzeug_anzeigename(wz)
