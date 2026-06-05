"""Arbeitsplan-Generator fuer Multi-Setup-Projekte.

Erzeugt aus einer Variante (Setups + Pausen) eine Checkliste, die
- als PDF gedruckt werden kann (neben CNC liegen)
- als Markdown/HTML in der UI angezeigt wird

Siehe Wiki: docs/wiki/Workflow-Modul.md
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from camwosa.db.models import Maschine
from camwosa.project.schema import Setup, SetupPause, Variante


def erzeuge_arbeitsplan_markdown(
    variante: Variante, projekt_name: str, maschine: Maschine
) -> str:
    """Erzeugt einen druckbaren Arbeitsplan als Markdown."""
    zeilen: list[str] = []
    zeilen.append(f"# Arbeitsplan: {projekt_name}")
    zeilen.append(f"**Variante:** {variante.name} · **Datum:** {datetime.now().strftime('%Y-%m-%d')}")
    zeilen.append(f"**Maschine:** {maschine.name}")
    zeilen.append(f"**Geschaetzte Gesamtzeit:** {_gesamtzeit(variante):.0f} min")
    zeilen.append("")

    nr = 1
    for setup in variante.setups:
        if setup.pause_vor:
            zeilen.append(_pause_md(setup.pause_vor, nr))
            nr += 1
        zeilen.append(_setup_md(setup, nr))
        nr += 1
    zeilen.append("")
    zeilen.append("[ ] FERTIG — Maschine ausschalten, Werkstueck entnehmen")
    return "\n".join(zeilen)


def erzeuge_arbeitsplan_pdf(
    variante: Variante,
    projekt_name: str,
    maschine: Maschine,
    *,
    ziel_pfad: str | Path | None = None,
) -> bytes:
    """Erzeugt einen druckbaren Arbeitsplan als PDF.

    Wenn ``ziel_pfad`` gesetzt: schreibt in Datei und gibt die Bytes zurueck.
    Sonst: gibt nur die Bytes zurueck.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=20 * mm,
        rightMargin=15 * mm,
        title=f"Arbeitsplan {projekt_name}",
    )
    styles = getSampleStyleSheet()
    titel = ParagraphStyle("titel", parent=styles["Title"], fontSize=18, spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceBefore=10)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12)

    elemente = []
    elemente.append(Paragraph(f"Arbeitsplan: {projekt_name}", titel))
    elemente.append(Paragraph(
        f"Variante: <b>{variante.name}</b> &nbsp; "
        f"Datum: {datetime.now().strftime('%Y-%m-%d')} &nbsp; "
        f"Maschine: {maschine.name} &nbsp; "
        f"Geschaetzt: {_gesamtzeit(variante):.0f} min",
        body,
    ))
    elemente.append(Spacer(1, 5 * mm))

    nr = 1
    for setup in variante.setups:
        if setup.pause_vor:
            elemente.append(_pause_pdf(setup.pause_vor, nr, h2, body))
            nr += 1
        elemente.append(_setup_pdf(setup, nr, h2, body))
        nr += 1

    elemente.append(Spacer(1, 5 * mm))
    elemente.append(Paragraph("[  ] FERTIG", h2))

    doc.build(elemente)
    bytes_data = buffer.getvalue()
    if ziel_pfad:
        Path(ziel_pfad).write_bytes(bytes_data)
    return bytes_data


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _gesamtzeit(variante: Variante) -> float:
    return sum(s.geschaetzte_zeit_minuten for s in variante.setups)


def _setup_md(setup: Setup, nr: int) -> str:
    ops = "\n".join(f"  - {o.name} (Werkzeug {o.parameter.get('werkzeug_id', '?')})"
                    for o in setup.operationen)
    return (
        f"## [{nr:2d}] [ ] Setup: {setup.name}\n"
        f"- Modus: {setup.maschinen_modus}\n"
        f"- Spannmittel: {setup.spannmittel or '-'}\n"
        f"- Werkzeug: {setup.werkzeug_id}\n"
        f"- Nullpunkt: X={setup.nullpunkt[0]:.1f} Y={setup.nullpunkt[1]:.1f} Z={setup.nullpunkt[2]:.1f}\n"
        f"- Geschaetzte Zeit: {setup.geschaetzte_zeit_minuten:.0f} min\n"
        f"- Operationen:\n{ops if ops else '  (keine)'}\n"
        + (f"- Notizen: {setup.notizen}\n" if setup.notizen else "")
    )


def _pause_md(pause: SetupPause, nr: int) -> str:
    return (
        f"## [{nr:2d}] [ ] PAUSE: {pause.titel}\n"
        f"- Typ: {pause.typ.value}\n"
        + (
            "- **Maschine ausschalten → eigene G-Code-Datei** "
            "(Umkabeln; Streaming-Verbindung wird getrennt)\n"
            if getattr(pause, "getrennte_datei", False) else ""
        )
        + f"- Anweisung:\n  {pause.anweisung.replace(chr(10), chr(10) + '  ')}\n"
        + (f"- Foto: {pause.foto_pfad}\n" if pause.foto_pfad else "")
    )


def _setup_pdf(setup: Setup, nr: int, h2, body):
    text = (
        f"<b>[{nr:2d}] [  ] Setup: {setup.name}</b><br/>"
        f"Modus: {setup.maschinen_modus} &nbsp; "
        f"Werkzeug: {setup.werkzeug_id} &nbsp; "
        f"Zeit: {setup.geschaetzte_zeit_minuten:.0f} min<br/>"
        f"Spannmittel: {setup.spannmittel or '-'} &nbsp; "
        f"Nullpunkt: X={setup.nullpunkt[0]:.1f} Y={setup.nullpunkt[1]:.1f} "
        f"Z={setup.nullpunkt[2]:.1f}"
    )
    if setup.operationen:
        text += "<br/><b>Operationen:</b><br/>"
        for op in setup.operationen:
            text += f"&nbsp;&nbsp;[ ] {op.name} ({op.typ})<br/>"
    if setup.notizen:
        text += f"<br/><i>{setup.notizen}</i>"
    return Paragraph(text, body)


def _pause_pdf(pause: SetupPause, nr: int, h2, body):
    text = (
        f"<b>[{nr:2d}] [  ] PAUSE: {pause.titel}</b><br/>"
        f"Typ: <i>{pause.typ.value}</i><br/>"
        + (
            "<b>Maschine ausschalten &rarr; eigene G-Code-Datei</b> "
            "(Umkabeln; Verbindung wird getrennt)<br/>"
            if getattr(pause, "getrennte_datei", False) else ""
        )
        + f"{pause.anweisung.replace(chr(10), '<br/>')}"
    )
    return Paragraph(text, body)


__all__ = [
    "erzeuge_arbeitsplan_markdown",
    "erzeuge_arbeitsplan_pdf",
]
