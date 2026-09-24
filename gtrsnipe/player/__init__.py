"""Player / visualizer for gtrsnipe Songs.

Turns a parsed + fretboard-mapped Song into a time-driven view of the neck:
a timeline of fretboard states (:mod:`gtrsnipe.player.timeline`), a clock that
paces them (:mod:`gtrsnipe.player.clock`), and renderers that paint each state
(:mod:`gtrsnipe.player.render`). The three layers are decoupled: any clock
combines with any renderer over the same ``Frame`` objects.
"""
from .frame import Frame
from .timeline import TimelineBuilder

__all__ = ["Frame", "TimelineBuilder"]
