"""Research tools behind the homograph work (see docs/dev/BACKLOG.md, step 2).

corpus   : read melody corpora (Essen kern, ABC collections, MIDI melody tracks)
           into one monophonic format, cached as gzipped JSON lines.
offsets  : the offset profile of two aligned melodies (richness, entropy,
           coverage, switches, total variation, reuse) from
           docs/dev/coupled_transposition_structure.md.
cli      : the ``gtrsnipe-research`` command.

None of this is imported by the converter, so it adds nothing to a plain
``gtrsnipe`` run.
"""
