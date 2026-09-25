"""Player / visualizer for gtrsnipe Songs.

Turns a parsed + fretboard-mapped Song into a time-driven view of the neck:
a timeline of fretboard states (:mod:`gtrsnipe.player.timeline`), an event-driven
Transport that paces them (:mod:`gtrsnipe.player.transport`), visual sinks
(:mod:`gtrsnipe.player.sink`), and renderers that paint each state
(:mod:`gtrsnipe.player.render`). The layers are decoupled over ``Frame`` objects.
"""
from .frame import Frame
from .timeline import TimelineBuilder

__all__ = ["Frame", "TimelineBuilder"]
