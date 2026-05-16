# Operations-Plugin-System

> **Status:** ✅ Phase E9 implementiert.
> **Code:** [backend/camwosa/cam/plugin.py](../../backend/camwosa/cam/plugin.py)

Erlaubt User-Code eigene CAM-Operationen zu registrieren — analog zum [Postprozessor-Plugin-System](Postprozessor-Plugins).

## Plugin schreiben

```python
from camwosa.cam.plugin import OperationPlugin, registry
from camwosa.gcode.toolpath import Toolpath, OperationsTyp, Bewegung, BewegungsTyp

OPERATION_ID = "meine_zickzack"


class ZickZackOperation(OperationPlugin):
    name = "Mein ZickZack"
    beschreibung = "Eigene Zickzack-Strategie"
    benoetigt_geschlossene_kontur = True

    def erzeuge_toolpath(self, geometrie, werkzeug, parameter):
        bewegungen = []
        # ... eigene Logik ...
        return Toolpath(
            operation_id="zickzack_1",
            operation_typ=OperationsTyp.TASCHE,
            werkzeug_id=werkzeug.id,
            spindel_rpm=parameter.get("spindel_rpm", 18000),
            sicherheitshoehe=5.0,
            bewegungen=bewegungen,
        )


registry().register("meine_zickzack", ZickZackOperation)
```

## Plugin laden

```python
from camwosa.cam.plugin import registry
from pathlib import Path

anzahl = registry().lade_aus_verzeichnis(Path("data/operations/user/"))
print(f"{anzahl} User-Operations geladen")
```

## Verwandt

- [Postprozessor-Plugins](Postprozessor-Plugins)
- [Operation-Kontur](Operation-Kontur), [Operation-Tasche](Operation-Tasche), [Operation-Bohren](Operation-Bohren), [Operation-Gravur](Operation-Gravur)
