"""Feeds & Speeds Subsystem."""

from camwosa.feeds.rechner import (
    FeedsSpeedsErgebnis,
    FeedsSpeedsWarnung,
    WarnungsStufe,
    berechne_feeds_speeds,
)

__all__ = [
    "FeedsSpeedsErgebnis",
    "FeedsSpeedsWarnung",
    "WarnungsStufe",
    "berechne_feeds_speeds",
]
