"""Test fuer Variante.annotationen (globale Annotationen auf Werkstueck-Ebene)."""

from __future__ import annotations

from camwosa.db.models import Rohmaterial, RohmaterialForm
from camwosa.project.schema import (
    GeometrieAnnotation,
    GeometrieAnnotationTyp,
    Variante,
)


def _rohmat() -> Rohmaterial:
    return Rohmaterial(
        form=RohmaterialForm.PLATTE,
        laenge=200, breite=200, hoehe=12,
        material_id="buche_massiv",
    )


def test_variante_default_keine_annotationen():
    v = Variante(id="v1", name="V1", rohmaterial=_rohmat())
    assert v.annotationen == []


def test_variante_mit_annotationen():
    a = GeometrieAnnotation(
        id="anschlag_1",
        typ=GeometrieAnnotationTyp.ANSCHLAGBOHRUNG,
        x=10, y=10, durchmesser_mm=3, tiefe_mm=8,
    )
    v = Variante(id="v1", name="V1", rohmaterial=_rohmat(), annotationen=[a])
    assert len(v.annotationen) == 1
    assert v.annotationen[0].typ == GeometrieAnnotationTyp.ANSCHLAGBOHRUNG


def test_variante_serialize_roundtrip_mit_annotationen():
    v = Variante(
        id="v1", name="V1", rohmaterial=_rohmat(),
        annotationen=[
            GeometrieAnnotation(
                id="r", typ=GeometrieAnnotationTyp.REFPUNKT, x=0, y=0,
            ),
            GeometrieAnnotation(
                id="b", typ=GeometrieAnnotationTyp.ANSCHLAGBOHRUNG,
                x=50, y=50, durchmesser_mm=4, tiefe_mm=10,
            ),
        ],
    )
    roh = v.model_dump(mode="json")
    wieder = Variante.model_validate(roh)
    assert len(wieder.annotationen) == 2
    assert wieder.annotationen[0].id == "r"
    assert wieder.annotationen[1].durchmesser_mm == 4
