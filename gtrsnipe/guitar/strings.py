"""String physics for retuning: tension, breaking pitch, and whether a string
at a given pitch is playable, floppy, too tight, or about to snap.

Tension (Mersenne/Taylor) in the imperial form string makers publish:
    T [lb] = UW [lb/in] * (2 * L [in] * f [Hz])**2 / 386.4

Plain steel: UW = rho * A, so the stress T/A = rho * (2 L f)**2 does NOT depend
on the gauge. A plain string therefore breaks at a pitch fixed by the scale
length alone -- f_break = sqrt(UTS/rho) / 2L, about A4 at 25.5" for music wire
(UTS ~2.7 GPa). A heavier high E doesn't help; the high E sits at ~53% of its
breaking stress at E4, 75% at G4, 94% at A4. That is why it's the one that snaps.

Wound: the core carries the load and the wrap only adds mass, so core stress =
rho * m * (2 L f)**2 with m = total/core mass. m depends on the (unpublished) core
size -- roughly 2-3 for a wound G, 4-6 for a low E -- so wound strings are judged
by TENSION (feel and neck load), with only a conservative pitch ceiling taken
from the thinnest plausible wrap (m >= 2). Plain steel has the lowest stress of
any string at a given pitch (m = 1), so a pitch that would break a plain string
is out of reach for every steel string.

Tuning down never breaks a string, but below ~55% of its normal tension
(about -5 semitones) it flops, buzzes and won't intonate.

Calibration: plain strings match D'Addario's published EXL110 tensions within
1%; nickel round-wound UW = 0.83 x solid steel of the same gauge fits their
.026/.036/.046 within 2%.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

GRAVITY_IN = 386.4          # in/s^2: converts lb-mass to lb-force in the formula
STEEL_DENSITY = 0.2836      # lb/in^3
STEEL_DENSITY_SI = 7850.0   # kg/m^3
WOUND_FACTOR = 0.83         # nickel round-wound UW / solid-steel UW, same outer gauge
WOUND_MIN_STRESS = 2.0      # a wound core carries >= ~2x plain steel's stress at a pitch
UTS_PSI = 2.7e9 / 6894.757  # music-wire ultimate tensile strength (~390 ksi)
BREAK_AT = 0.90             # stress >= 90% of UTS: treat as breaking
RISKY_AT = 0.70             # stress >= 70% of UTS: snap risk (high E past F#4)
SLACK_BELOW = 0.55          # tension < 55% of the string's normal: floppy
TIGHT_ABOVE = 1.45          # tension > 145% of normal: stiff, hard on the neck
HAZARD_ABOVE = 2.0          # tension >= 2x normal: bridge/neck hazard even if the core holds

PLAIN_GAUGES = [.007, .008, .0085, .009, .0095, .010, .0105, .011, .0115, .012, .013,
                .0135, .014, .015, .016, .017, .018, .019, .020, .022, .024, .026]
WOUND_GAUGES = [.017, .018, .020, .021, .022, .024, .026, .028, .030, .032, .034, .036,
                .038, .039, .042, .044, .046, .048, .049, .052, .054, .056, .059, .062,
                .064, .066, .068, .070, .072, .074, .080, .085, .090, .095, .100, .105,
                .110, .120, .130, .135, .145]


def hz(pitch: float) -> float:
    return 440.0 * 2 ** ((pitch - 69) / 12)


@dataclass(frozen=True)
class Gauge:
    inches: float
    wound: bool

    @property
    def unit_weight(self) -> float:
        """Mass per inch (lb/in)."""
        solid = STEEL_DENSITY * math.pi * self.inches ** 2 / 4
        return solid * WOUND_FACTOR if self.wound else solid

    def __str__(self) -> str:
        s = f"{self.inches:.4f}".rstrip("0")
        s = s[1:] if s.startswith("0") else s
        if len(s) < 4:
            s += "0" * (4 - len(s))
        return s + ("w" if self.wound else "")


def parse_gauges(spec: str) -> List[Gauge]:
    """String gauges -> a list ordered LOW string -> high, like --tuning-pitches.

    Written thin->thick as sets usually are ('10 13 17 26w 36w 46w', '.010,...'),
    they're flipped; thick->thin is already low->high; a mixed order (a
    re-entrant set, e.g. Nashville) is taken as given, low string first.
    Suffix w = wound, p = plain; unsuffixed gauges above .020 are wound."""
    out = []
    for tok in re.split(r"[,\s]+", spec.strip()):
        if not tok:
            continue
        m = re.fullmatch(r"(\d*\.?\d+)([wWpP]?)", tok)
        if not m:
            raise ValueError(f"bad string gauge {tok!r} (use e.g. .010 or .046w)")
        v = float(m.group(1))
        if v >= 1:                      # '46' means .046
            v /= 1000.0
        wound = m.group(2).lower() == "w" or (not m.group(2) and v > 0.0205)
        out.append(Gauge(v, wound))
    if not out:
        raise ValueError("no string gauges given")
    d = [g.inches for g in out]
    if len(set(d)) > 1 and all(a <= b for a, b in zip(d, d[1:])):
        out.reverse()                   # thin -> thick: the usual set notation
    return out


def tension_lb(g: Gauge, pitch: float, scale_in: float) -> float:
    return g.unit_weight * (2 * scale_in * hz(pitch)) ** 2 / GRAVITY_IN


def plain_stress(pitch: float, scale_in: float) -> float:
    """Stress in plain steel at ``pitch`` as a fraction of its breaking strength:
    rho*(2Lf)^2 -- the same for every gauge."""
    return tension_lb(Gauge(0.010, False), pitch, scale_in) / (math.pi * 0.010 ** 2 / 4) / UTS_PSI


def stress_fraction(g: Gauge, pitch: float, scale_in: float) -> Optional[float]:
    """Stress as a fraction of breaking strength, for plain strings. None for
    wound ones: their core size isn't known, so they're judged by tension."""
    return None if g.wound else plain_stress(pitch, scale_in)


def breaking_pitch_hz(scale_in: float) -> float:
    """The pitch at which ANY steel string of this scale reaches BREAK_AT of its
    strength (plain steel, the best case -- independent of gauge)."""
    v = math.sqrt(2.7e9 * BREAK_AT / STEEL_DENSITY_SI)          # m/s
    return v / (2 * scale_in * 0.0254)


@dataclass
class StringState:
    pitch: int
    tension: float
    ratio: float                 # tension / the string's normal tension
    stress: Optional[float]      # fraction of breaking strength (plain only)
    status: str                  # ok | slack | tight | breaks | impossible
    suggestion: Optional[Tuple[Gauge, float]] = None    # (gauge, tension) to restring

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _status(g: Gauge, pitch: int, normal_t: float, scale_in: float
            ) -> Tuple[str, float, float, Optional[float]]:
    t = tension_lb(g, pitch, scale_in)
    ps = plain_stress(pitch, scale_in)
    load = ps * (WOUND_MIN_STRESS if g.wound else 1.0)   # wound: a conservative floor
    ratio = t / normal_t if normal_t else 1.0
    if hz(pitch) >= breaking_pitch_hz(scale_in):
        st = "impossible"
    elif load >= BREAK_AT or ratio >= HAZARD_ABOVE:
        st = "breaks"
    elif load >= RISKY_AT or ratio > TIGHT_ABOVE:
        st = "tight"
    elif ratio < SLACK_BELOW:
        st = "slack"
    else:
        st = "ok"
    return st, t, ratio, (None if g.wound else ps)


def restring(pitch: int, target_tension: float, scale_in: float) -> Optional[Tuple[Gauge, float]]:
    """The catalog gauge whose tension at ``pitch`` is closest to
    ``target_tension`` (the feel of the string it replaces) and safe."""
    best = None
    ps = plain_stress(pitch, scale_in)
    for inches, wound in [(g, False) for g in PLAIN_GAUGES] + [(g, True) for g in WOUND_GAUGES]:
        g = Gauge(inches, wound)
        if ps * (WOUND_MIN_STRESS if wound else 1.0) >= RISKY_AT:
            continue
        t = tension_lb(g, pitch, scale_in)
        if best is None or abs(t - target_tension) < abs(best[1] - target_tension):
            best = (g, t)
    return best


@dataclass
class Instrument:
    """A strung instrument: scale length, gauges and the pitches they're strung
    for. Lists are indexed like the rest of gtrsnipe: 0 = HIGHEST string."""
    scale_in: float
    gauges: List[Gauge]
    nominal: List[int]
    name: str = ""

    def normal_tension(self, s: int) -> float:
        return tension_lb(self.gauges[s], self.nominal[s], self.scale_in)

    def assess(self, s: int, pitch: int) -> StringState:
        st, t, ratio, sf = _status(self.gauges[s], pitch, self.normal_tension(s), self.scale_in)
        state = StringState(pitch, t, ratio, sf, st)
        if st in ("slack", "tight", "breaks"):
            state.suggestion = restring(pitch, self.normal_tension(s), self.scale_in)
        return state

    def describe(self) -> str:
        gs = "-".join(str(g).lstrip(".").rstrip("w") for g in (self.gauges[0], self.gauges[-1]))
        return f'{self.name or gs} set, {self.scale_in:g}" scale'


# Conventional sets, keyed by the tuning each is designed for (gauges LOW -> high).
# Any other tuning gets a set designed for it, so "normal tension" stays physical
# (a 10-46 set in DROP_C would make C2 the low string's "normal").
_SETS = {
    "STANDARD": ("10-46", 25.5, ".046w .036w .026w .017 .013 .010"),
    "SEVEN_STRING_STANDARD": ("10-59", 25.5, ".059w .046w .036w .026w .017 .013 .010"),
    "BARITONE_B": ("13-62", 27.0, ".062w .046w .036w .026w .017 .013"),
    "BASS_STANDARD": ("45-105", 34.0, ".105w .085w .065w .045w"),
}


def _balanced_gauge(pitch: int, scale_in: float, target: float) -> Gauge:
    """The catalog gauge giving ~``target`` lb at ``pitch`` (plain if thin enough)."""
    uw = target * GRAVITY_IN / (2 * scale_in * hz(pitch)) ** 2
    d_plain = math.sqrt(4 * uw / (math.pi * STEEL_DENSITY))
    if d_plain <= 0.0205:
        return Gauge(min(PLAIN_GAUGES, key=lambda g: abs(g - d_plain)), False)
    d_wound = math.sqrt(4 * uw / (math.pi * STEEL_DENSITY * WOUND_FACTOR))
    return Gauge(min(WOUND_GAUGES, key=lambda g: abs(g - d_wound)), True)


def _default_scale(tuning: str, nominal: Sequence[int]) -> float:
    if tuning.startswith("BASS_"):
        return 34.0
    if tuning.startswith("BARITONE_"):
        return 27.0
    lowest, highest = min(nominal), max(nominal)
    if lowest <= 31 and highest <= 50:     # low AND tops out by D3: a bass
        return 34.0
    if lowest <= 35:                       # baritone / extended-range guitar (7-, 8-string)
        return 27.0
    return 25.5


def default_instrument(tuning: str, nominal_high_to_low: Sequence[int],
                       scale_in: Optional[float] = None,
                       gauges_low_to_high: Optional[Sequence[Gauge]] = None) -> Instrument:
    """The strung instrument a tuning implies: the conventional set when the tuning
    is the one that set is designed for (STANDARD 10-46, 7-string 10-59, BARITONE_B
    13-62, BASS_STANDARD 45-105), else a balanced ~17 lb/string (~42 lb bass) set
    designed for the tuning. ``scale_in`` / ``gauges_low_to_high`` override."""
    n = len(nominal_high_to_low)
    t = (tuning or "").upper()
    conventional = _SETS.get(t)
    if conventional and len(conventional[2].split()) != n:
        conventional = None
    if gauges_low_to_high:
        if len(gauges_low_to_high) != n:
            raise ValueError(f"{len(gauges_low_to_high)} string gauges for a {n}-string tuning")
        scale = scale_in or (conventional[1] if conventional else _default_scale(t, nominal_high_to_low))
        return Instrument(scale, list(reversed(gauges_low_to_high)), list(nominal_high_to_low), "")
    if conventional:
        name, default, spec = conventional
        return Instrument(scale_in or default, list(reversed(parse_gauges(spec))),
                          list(nominal_high_to_low), name)
    scales = [scale_in] if scale_in else [_default_scale(t, nominal_high_to_low), 25.5, 24.75]
    for scale in dict.fromkeys(scales):
        target = 42.0 if scale >= 30 else 17.0
        gl = [_balanced_gauge(p, scale, target) for p in reversed(nominal_high_to_low)]
        inst = Instrument(scale, list(reversed(gl)), list(nominal_high_to_low), "balanced")
        if all(inst.assess(s, p).ok for s, p in enumerate(nominal_high_to_low)):
            break                          # this scale can hold every string's own pitch
    return inst
