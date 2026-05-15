# GRBL Genmitsu Postprozessor

> **Status:** ✅ Implementiert.
> **Code:** [backend/camwosa/postprocessor/grbl_genmitsu.py](../../backend/camwosa/postprocessor/grbl_genmitsu.py)

Erbt vom [GRBL-Standard-Postprozessor](Postprozessor-GRBL.md) und ergaenzt einen Header-Hinweis fuer Genmitsu-Maschinen (Maschinen-Modus, $101-Pruefung).

```python
from camwosa.postprocessor import registry
post = registry().get("grbl_genmitsu")()
```

Beispiel-Output:

```
; CAMWOSA G-Code
; Maschinen-Modus: standard_xyz (bitte $101 in CNCjs pruefen!)
; Maschine: Genmitsu ProVerXL 4030 V2
; Werkzeug: 6mm Schaftfraeser ...
G21
G90
...
```

## Wann nutzen

Standard-Wahl fuer alle Genmitsu-Maschinen (PROVer, ProVerXL, …) ohne Rotary. Fuer Rotary siehe [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md).

## Verwandt

- [Postprozessor-GRBL](Postprozessor-GRBL.md)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md)
- [Maschinenprofil-Format](Maschinenprofil-Format.md)
