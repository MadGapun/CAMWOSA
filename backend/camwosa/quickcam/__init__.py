"""Quick-CAM: kuratierte Vorlagen fuer einfache Einzelfraesaufgaben.

Statt einem leeren Projekt + manueller Konfiguration startet der User
ein Quick-CAM-Template ("Tasche", "Schriftzug", "Bohrloch-Muster",
"Kontur ausschneiden") und bekommt direkt eine lauffaehige Operation.

Templates sind in templates.py definiert — neue Templates kommen ohne
Aenderung am Frontend dazu (Backend listet sie auf).
"""

from camwosa.quickcam.templates import (
    QuickCAMTemplate,
    erzeuge_aus_template,
    template_index,
    templates,
)

__all__ = [
    "QuickCAMTemplate",
    "erzeuge_aus_template",
    "template_index",
    "templates",
]
