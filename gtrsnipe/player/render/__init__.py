"""Renderers paint a :class:`~gtrsnipe.player.frame.Frame` onto some surface.

Every renderer consumes the same ``Frame`` objects the timeline produces, so a
clock policy and a render target compose freely. The MVP ships an ASCII
fretboard renderer; browser / Qt renderers can join here later without touching
the timeline or clock layers.
"""
from .ascii import AsciiFretboardRenderer

__all__ = ["AsciiFretboardRenderer"]
