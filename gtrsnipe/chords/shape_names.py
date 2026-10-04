"""Shape-relative chord names (``--shape-names``): the "generalized capo".

A guitarist in baritone B or E-flat thinks in the shapes of standard tuning: the
fingering of a C chord is "a C shape" whatever it sounds like. When a tuning is the
standard tuning shifted by the same amount on every string (E_FLAT -1, D_STANDARD -2,
the baritones -4, -5, -7), every chord is the shape's chord moved by that amount, and
a capo adds to it. Shape names name the fingering: concert pitch minus the shift.

For a drop or open tuning the strings don't move together, so its shapes have no
standard names; names stay in concert pitch, and the banner says so. The banner is
always shown, so a reader never mistakes one convention for the other.
"""
from dataclasses import dataclass, replace
from typing import List, Optional

from ..core.chords import Chord
from ..core.keys import spell_free
from ..core.theory import note_name_to_pitch
from ..core.types import Tuning

# The standard tuning a shape is named in, by string count.
_REFERENCE = {6: "STANDARD", 7: "SEVEN_STRING_STANDARD", 4: "BASS_STANDARD"}


@dataclass
class ShapeNaming:
    shift: int            # semitones added to a sounding chord to name its shape
    active: bool          # False: names stay in concert pitch
    banner: str

    def name(self, chord: Optional[Chord]) -> str:
        """The chord's name under this convention ("N.C." for no chord)."""
        if chord is None:
            return "N.C."
        return transpose(chord, self.shift).name if self.active else chord.name


def transpose(chord: Chord, semitones: int) -> Chord:
    """The same chord moved by ``semitones`` (root and bass), and its key with it."""
    bass = None if chord.bass is None else (chord.bass + semitones) % 12
    key = chord.key.transposed(semitones) if chord.key is not None else None
    return replace(chord, root=(chord.root + semitones) % 12, bass=bass, key=key)


def shape_naming(tuning_names_low_to_high: List[str], capo: int = 0,
                 label: str = "") -> ShapeNaming:
    """The shape-naming convention for a tuning (note names, low string first)."""
    label = label or ",".join(tuning_names_low_to_high)
    n = len(tuning_names_low_to_high)
    ref = _REFERENCE.get(n)
    if ref is None:
        return ShapeNaming(0, False, f"Shape names: there's no standard {n}-string tuning to "
                                     "name shapes in, so chord names are concert pitch.")
    target = [note_name_to_pitch(x) for x in tuning_names_low_to_high]
    reference = [note_name_to_pitch(x) for x in Tuning[ref].value]
    offsets = {t - r for t, r in zip(target, reference)}
    if len(offsets) != 1:
        return ShapeNaming(0, False, f"Shape names: {label} isn't {ref} shifted evenly on every "
                                     "string, so its shapes have no standard names; chord names "
                                     "are concert pitch.")
    k = offsets.pop() + capo                  # sounding = shape + k
    ref_text = f"{ref}" + ("" if n == 6 else " tuning")
    if k % 12 == 0:
        return ShapeNaming(0, True, f"Shape names: named as in {ref_text} with no capo, which "
                                    "here is also concert pitch.")
    direction = "lower" if k < 0 else "higher"
    steps = abs(k)
    return ShapeNaming(-k, True,
                       f"Shape names: chords are named by the shape you finger, as in {ref_text} "
                       f"with no capo. Everything sounds {steps} semitone{'s' if steps != 1 else ''} "
                       f"{direction}: a C shape sounds {spell_free(k % 12)}.")


def shape_naming_for_config(cfg) -> ShapeNaming:
    """The convention for a MapperConfig (its tuning, custom tuning and capo)."""
    if getattr(cfg, "custom_tuning", None):
        names, label = list(cfg.custom_tuning), "this tuning"
    else:
        names, label = list(Tuning[cfg.tuning].value), cfg.tuning
    return shape_naming(names, getattr(cfg, "capo", 0) or 0, label)
