"""Chord-chart output: break a Song into per-measure chords and print a sheet.

Segmentation (:mod:`gtrsnipe.chords.segment`) turns a Song into one chord per
measure; the chart builder (:mod:`gtrsnipe.chords.chart`) names each chord (via
:mod:`gtrsnipe.core.chords`), voices a representative fingering with the existing
mapper, and lays it out as a Markdown/ASCII chord sheet.
"""
from .segment import ChordSpan, segment_by_measure

__all__ = ["ChordSpan", "segment_by_measure"]
