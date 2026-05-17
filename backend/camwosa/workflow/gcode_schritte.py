"""G-Code-Generierung anhand einer Schritt-Liste (Multi-Werkzeug pro Setup).

Aufruf:
    schreibe_gcode_aus_schritten(setup, maschine, werkzeug_index,
                                  toolpaths_pro_operation, ziel)

Algorithmus:
1. Schritte werden in Bloecke gegliedert: jeder Werkzeugwechsel mit Strategie
   SEPARATE_DATEI bricht den aktuellen Block ab; alles bis dahin landet in der
   gleichen G-Code-Datei.
2. INLINE_M6 / INLINE_MAKRO bleiben im selben Block — Postprozessor schreibt
   ``M6 T<n> M0`` bzw. den Makro-Aufruf an die Stelle.
3. ManualNCSchritt-Zeilen werden 1:1 eingebettet (mit Sicherheits-Aufstieg
   davor wenn ``sicher_anfahren=True``).
4. PauseSchritt/UmspannSchritt sind Hinweise an den User — kein G-Code.
5. AchsWechselSchritt bricht IMMER auf neue Datei.

So bekommt der User bei „Schruppen + Schlichten":
- Setup mit 3 Schritten: [OP Schruppen, WW (SEPARATE_DATEI), OP Schlichten]
- → 2 Dateien: setup_01a_schruppen.nc + setup_01b_schlichten.nc
- Beide nutzen denselben Nullpunkt — der User wechselt einfach das Werkzeug

Bei einem Werkzeugwechsel mit INLINE_M6:
- → 1 Datei mit M6 + M0 dazwischen
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from camwosa.db.models import Maschine, Werkzeug
from camwosa.gcode.toolpath import Toolpath
from camwosa.postprocessor import PostKontext, registry
from camwosa.project.schritte import (
    AchsWechselSchritt,
    ArbeitsSchritt,
    ManualNCSchritt,
    OperationSchritt,
    PauseSchritt,
    UmspannSchritt,
    WerkzeugWechselSchritt,
    WerkzeugWechselStrategie,
)


@dataclass
class GcodeBlock:
    """Ein zusammenhaengender G-Code-Block — eine Datei."""

    index: int
    werkzeug: Werkzeug
    titel: str
    toolpaths: list[Toolpath]
    inline_zeilen: list[tuple[int, list[str]]]
    """``(position, zeilen)`` — Position relativ zur Toolpath-Liste, danach werden
    die zusaetzlichen Zeilen vor dem n-ten Toolpath eingefuegt."""


def gliedere_schritte_in_bloecke(
    schritte: Iterable[ArbeitsSchritt],
    *,
    werkzeug_index: dict[str, Werkzeug],
    toolpaths_pro_operation: dict[str, list[Toolpath]],
    start_werkzeug: Werkzeug | None,
) -> list[GcodeBlock]:
    """Gliedert eine Schritt-Liste in G-Code-Bloecke.

    ``start_werkzeug`` ist das anfaenglich montierte Werkzeug (vor Schritt 0).
    Wenn None: der erste WW-Schritt definiert das Werkzeug.

    Returns: Liste von GcodeBlock. Leere Bloecke werden ausgelassen.
    """
    bloecke: list[GcodeBlock] = []
    aktuelles_wz: Werkzeug | None = start_werkzeug
    aktuelle_paths: list[Toolpath] = []
    aktuelle_inline: list[tuple[int, list[str]]] = []
    block_titel = _safe(start_werkzeug.name) if start_werkzeug else "block_01"
    block_idx = 1

    def schliesse_block():
        nonlocal aktuelle_paths, aktuelle_inline, block_idx
        if aktuelle_paths or aktuelle_inline:
            bloecke.append(GcodeBlock(
                index=block_idx,
                werkzeug=aktuelles_wz,  # type: ignore[arg-type]
                titel=block_titel,
                toolpaths=list(aktuelle_paths),
                inline_zeilen=list(aktuelle_inline),
            ))
            block_idx += 1
        aktuelle_paths = []
        aktuelle_inline = []

    for s in schritte:
        if not s.aktiviert:
            continue
        if isinstance(s, WerkzeugWechselSchritt):
            neues_wz = werkzeug_index.get(s.werkzeug_neu_id)
            if neues_wz is None:
                raise KeyError(
                    f"WerkzeugWechselSchritt verweist auf unbekanntes Werkzeug '{s.werkzeug_neu_id}'"
                )
            if s.strategie == WerkzeugWechselStrategie.SEPARATE_DATEI:
                schliesse_block()
                aktuelles_wz = neues_wz
                block_titel = f"{block_idx:02d}_{_safe(neues_wz.name)}"
            elif s.strategie == WerkzeugWechselStrategie.INLINE_M6:
                aktuelle_inline.append((
                    len(aktuelle_paths),
                    [
                        f"; --- Werkzeugwechsel: {s.werkzeug_alt_id or '?'} -> {neues_wz.id}",
                        f"M6 T{_tool_nummer(neues_wz)}",
                        "M0  ; warten auf User-Wechsel",
                    ] + (
                        ["G38.2 Z-20 F50  ; Z-Probe nach Wechsel"]
                        if s.z_probe_nach_wechsel else []
                    ),
                ))
                aktuelles_wz = neues_wz
            elif s.strategie == WerkzeugWechselStrategie.INLINE_MAKRO:
                makro = s.makro_name or "TOOLCHANGE"
                aktuelle_inline.append((
                    len(aktuelle_paths),
                    [
                        f"; --- Werkzeugwechsel via Makro '{makro}'",
                        f"; %wait",
                        f"; %{makro}  T={_tool_nummer(neues_wz)}",
                    ],
                ))
                aktuelles_wz = neues_wz
        elif isinstance(s, AchsWechselSchritt):
            schliesse_block()
            block_titel = f"{block_idx:02d}_{_safe(s.modus_neu)}"
        elif isinstance(s, OperationSchritt):
            paths = toolpaths_pro_operation.get(s.operation_id, [])
            aktuelle_paths.extend(paths)
        elif isinstance(s, ManualNCSchritt):
            zeilen = list(s.gcode_zeilen)
            if s.sicher_anfahren:
                zeilen.insert(0, "G0 Z5  ; sicher anfahren")
            aktuelle_inline.append((len(aktuelle_paths), zeilen))
        elif isinstance(s, (PauseSchritt, UmspannSchritt)):
            # Reine Mensch-Pausen — keine G-Code-Auswirkung,
            # Arbeitsplan kennt sie aber bereits aus dem Setup
            continue

    schliesse_block()
    return bloecke


def schreibe_gcode_aus_schritten(
    setup,  # type: ignore[no-untyped-def]
    maschine: Maschine,
    werkzeug_index: dict[str, Werkzeug],
    toolpaths_pro_operation: dict[str, list[Toolpath]],
    ziel_verzeichnis: str | Path,
) -> list[Path]:
    """Schreibt die G-Code-Dateien fuer ein Setup mit Schritt-Liste.

    Kann mehrere Dateien erzeugen (eine pro Block / pro Werkzeug bei
    SEPARATE_DATEI-Strategie). Gibt die Liste der geschriebenen Pfade zurueck.
    """
    ziel = Path(ziel_verzeichnis)
    ziel.mkdir(parents=True, exist_ok=True)

    schritte = setup.effektive_schritte()
    start_wz = werkzeug_index.get(setup.werkzeug_id)
    bloecke = gliedere_schritte_in_bloecke(
        schritte,
        werkzeug_index=werkzeug_index,
        toolpaths_pro_operation=toolpaths_pro_operation,
        start_werkzeug=start_wz,
    )

    geschrieben: list[Path] = []
    for block in bloecke:
        post_klasse = registry().get(maschine.postprozessor)
        post = post_klasse()
        ctx = PostKontext(maschine=maschine, werkzeug=block.werkzeug)

        # Toolpaths gemischt mit Inline-Zeilen
        zeilen = post.post_anfang(ctx) if hasattr(post, "post_anfang") else []
        inline_map = dict(block.inline_zeilen)  # position -> zeilen
        for idx, tp in enumerate(block.toolpaths):
            if idx in inline_map:
                zeilen.extend(inline_map[idx])
            zeilen.extend(post.post_einzeln(ctx, tp) if hasattr(post, "post_einzeln") else [])
        # Inline-Block am Ende
        if len(block.toolpaths) in inline_map:
            zeilen.extend(inline_map[len(block.toolpaths)])
        if hasattr(post, "post_ende"):
            zeilen.extend(post.post_ende(ctx))

        # Fallback: wenn der Post diese Helpers nicht hat, alte post_alle benutzen
        if not zeilen and block.toolpaths:
            zeilen = post.post_alle(ctx, block.toolpaths)
            # Inline-Zeilen werden hier am Anfang eingestreut (best effort)
            extra = [z for _, group in block.inline_zeilen for z in group]
            zeilen = extra + zeilen

        ext = post.file_extension
        pfad = ziel / f"{setup.id}_b{block.index:02d}_{block.titel}{ext}"
        pfad.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
        geschrieben.append(pfad)

    return geschrieben


def _tool_nummer(werkzeug: Werkzeug) -> int:
    """Mappe Werkzeug auf eine GRBL-Tn-Nummer.

    Hash der ID auf 1..99 — fuer GRBL ohne ATC reicht das.
    Wenn der User feste Slots will, kann er sie ueber das Werkzeug-Notiz-Feld pflegen.
    """
    h = abs(hash(werkzeug.id)) % 99 + 1
    return h


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


__all__ = [
    "GcodeBlock",
    "gliedere_schritte_in_bloecke",
    "schreibe_gcode_aus_schritten",
]
