"""``gtrsnipe-research``: corpus caches and offset profiles.

    gtrsnipe-research corpus list
    gtrsnipe-research corpus build essen [--data DIR]
    gtrsnipe-research corpus info essen
    gtrsnipe-research corpus show essen:deut4659
    gtrsnipe-research profile essen:deut4659#p1 essen:deut4659#p3
    gtrsnipe-research profile a.mid:2@1-16 "C4 D4 E4 C4" --rhythm sequence
    gtrsnipe-research families mtc-ann
    gtrsnipe-research scan essen mtc-fs --solve 50 --tabs out/

A song is a corpus reference (``NAME:ID``, optionally ``@START-END`` in notes,
1-based inclusive, or ``#pN`` for phrase N), or anything ``--homograph`` reads:
a .mid[:TRACK]/.abc/.tab/.vex file with an optional ``@START-END`` onset window,
or an inline melody.
"""
from __future__ import annotations

import argparse
import os
import re
import statistics
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import corpus as C
from .offsets import format_profile, profile_json, profile_songs

_loaded: Dict[str, List[C.Melody]] = {}


def _cache_path(name: str, data: Optional[str]) -> str:
    if os.path.exists(name) and name.endswith(".gz"):
        return name
    if name not in C.CORPORA:
        raise ValueError(f"unknown corpus {name!r} (known: {', '.join(C.CORPORA)})")
    path = C.default_cache(name, data)
    if not os.path.exists(path):
        raise ValueError(f"no cache for {name} yet: run  gtrsnipe-research corpus build {name}")
    return path


def _melodies(name: str, data: Optional[str]) -> List[C.Melody]:
    path = _cache_path(name, data)
    if path not in _loaded:
        _loaded[path] = C.read_cache(path)[1]
    return _loaded[path]


_REF = re.compile(r"^(?P<corpus>[a-z0-9-]+):(?P<id>.+?)(?:@(?P<s>\d+)-(?P<e>\d+)|#p(?P<p>\d+))?$")


def resolve_melody(ref: str, data: Optional[str]) -> Optional[C.Melody]:
    """A corpus reference as a Melody, or None if ``ref`` isn't one."""
    m = _REF.match(ref)
    if not m or m.group("corpus") not in C.CORPORA or os.path.exists(ref):
        return None
    mel = C.find(_melodies(m.group("corpus"), data), m.group("id"))
    if m.group("s"):
        return mel.slice(int(m.group("s")) - 1, int(m.group("e")))
    if m.group("p"):
        spans = mel.phrase_spans()
        k = int(m.group("p"))
        if not 1 <= k <= len(spans):
            raise ValueError(f"{mel.ref} has {len(spans)} phrase(s); no phrase {k}")
        out = mel.slice(*spans[k - 1])
        out.id = f"{mel.id}#p{k}"
        return out
    return mel


def load_song(spec: str, data: Optional[str]):
    """(Song, label) for a corpus reference, file or inline melody."""
    mel = resolve_melody(spec, data)
    if mel is not None:
        return mel.to_song(), mel.ref
    from ..arguments import setup_parser
    from ..converter import _load_homograph_song
    args = setup_parser().parse_args([])
    song, title, _ = _load_homograph_song(spec, args, anchor_open=[])
    return song, title


# -- commands ---------------------------------------------------------------------

def cmd_corpus_list(a) -> int:
    for name, spec in C.CORPORA.items():
        try:
            path = C.default_cache(name, a.data)
            state = "cached" if os.path.exists(path) else "not built"
        except ValueError:
            state = "no corpus root"
        print(f"{name:12} {state:10} {spec.about}")
    return 0


def cmd_corpus_build(a) -> int:
    def progress(i, n):
        if i == n or i % max(1, n // 20) == 0:
            print(f"\r  {i}/{n} files", end="", file=sys.stderr, flush=True)
    h = C.build(a.name, root=a.data, out=a.out, workers=a.workers, limit=a.limit,
                progress=progress)
    print(file=sys.stderr)
    print(f"{a.name}: {h['melodies']} melodies from {h['files']} files, {h['errors']} errors"
          f" -> {a.out or C.default_cache(a.name, a.data)}")
    for rel, err in h["error_sample"][:10]:
        print(f"  {rel}: {err}")
    return 0


def cmd_corpus_info(a) -> int:
    path = _cache_path(a.name, a.data)
    head = C.cache_header(path)
    lengths, sources, meters, phrases, dropped = [], Counter(), Counter(), 0, 0
    for m in C.iter_cache(path):
        lengths.append(len(m))
        sources[m.source.split(" ")[0] if m.source.startswith("midi:track") else m.source] += 1
        meters[m.meter or "?"] += 1
        phrases += bool(m.phrases)
        dropped += m.dropped
    print(f"{head['corpus']}: {head['about']}")
    print(f"  built {head['built']} with gtrsnipe {head['gtrsnipe']}; {head['files']} files, "
          f"{head['errors']} unreadable")
    if not lengths:
        print("  (no melodies)")
        return 0
    q = statistics.quantiles(lengths, n=4) if len(lengths) > 1 else [lengths[0]] * 3
    print(f"  {len(lengths)} melodies, {sum(lengths):,} notes; notes per melody median "
          f"{statistics.median(lengths):g} (IQR {q[0]:g}-{q[2]:g}, min {min(lengths)}, "
          f"max {max(lengths)})")
    print("  line from: " + ", ".join(f"{k} {v}" for k, v in sources.most_common()))
    print("  meters: " + ", ".join(f"{k} {v}" for k, v in meters.most_common(8)))
    print(f"  phrase-marked: {phrases}; simultaneous notes dropped: {dropped:,}")
    return 0


def cmd_corpus_show(a) -> int:
    from ..core.theory import pitch_to_note_name
    mel = resolve_melody(a.ref, a.data)
    if mel is None:
        raise ValueError(f"{a.ref!r} is not a corpus reference (NAME:ID)")
    print(f"{mel.ref}  {mel.title!r}" + (f" by {mel.artist}" if mel.artist else ""))
    print(f"  {len(mel)} notes, meter {mel.meter or '?'}, key {mel.key or '?'}, "
          f"from {mel.source}; phrases {len(mel.phrase_spans())}")
    starts = set(mel.phrases)
    toks = []
    for i, (p, t, d) in enumerate(zip(mel.pitches, mel.onsets, mel.durations)):
        dur = d / C.TPQ
        toks.append(("| " if i in starts and i else "") + pitch_to_note_name(p)
                    + ("" if dur == 1 else f":{dur:g}"))
    print("  " + " ".join(toks))
    return 0


def cmd_profile(a) -> int:
    (sa, la), (sb, lb) = load_song(a.a, a.data), load_song(a.b, a.data)
    rhythm = a.rhythm if a.rhythm in ("strict", "sequence") else float(a.rhythm)
    prof, why = profile_songs(sa, sb, rhythm=rhythm, subdivide=a.subdivide)
    if prof is None:
        print(f"{la} and {lb} don't align: {why}", file=sys.stderr)
        return 1
    if a.json:
        print(profile_json(prof, a=la, b=lb))
    else:
        print(f"A = {la}\nB = {lb}")
        print(format_profile(prof))
    return 0


def cmd_families(a) -> int:
    from .families import format_results, results_json, run
    path = _cache_path(a.name, a.data)
    head, mels = C.read_cache(path)
    if not any(m.family for m in mels):
        raise ValueError(f"{a.name} has no tune-family labels (try mtc-ann or mtc-fs)")
    res = run(mels, grid=a.grid, bootstrap=a.bootstrap, seed=a.seed,
              max_queries=a.queries, models=not a.no_models)
    res["corpus"] = head["corpus"]
    print(format_results(res, head["corpus"]))
    if a.json:
        with open(a.json, "w") as f:
            f.write(results_json(res))
    return 0


def cmd_scan(a) -> int:
    import json
    from . import scan as S
    mels, names = [], []
    for name in a.names:
        head, ms = C.read_cache(_cache_path(name, a.data))
        if a.named_melodies:                 # drop MIDI lines taken from the skyline
            ms = [m for m in ms if m.source != "midi:skyline"]
        mels += ms
        names.append(head["corpus"])
    by_ref = {m.ref: m for m in mels}
    stats, top, samples = S.scan(mels, unit=a.unit, max_richness=a.max_richness,
                                 min_len=a.min_len, max_len=a.max_len, window=a.window,
                                 stride=a.stride, keep=a.keep, min_keep_len=a.min_keep_len,
                                 sample_per_length=a.physics_sample,
                                 cross_corpus=a.cross_corpus, seed=a.seed)
    print(S.format_stats(stats, " + ".join(names)))
    for c in top[:a.solve]:
        c.solved = S.solve(c, by_ref)
    physics = {}
    for L, cs in samples.items():
        for c in cs:
            c.solved = S.solve(c, by_ref)
        physics[L] = {"sampled": len(cs),
                      "free": sum(bool(c.solved["free"]) for c in cs),
                      "anchored": sum(bool(c.solved["anchored"]) for c in cs),
                      "anchored_no_regauge": sum(bool(c.solved["anchored"])
                                                 and not c.solved["anchored"]["regauges"]
                                                 for c in cs),
                      "middle": sum(bool(c.solved["middle"]) for c in cs),
                      "middle_no_regauge": sum(bool(c.solved["middle"])
                                               and not c.solved["middle"]["regauges"] for c in cs)}
    if physics:
        print("\nPhysical check of random unrelated-sounding eligible pairs (share solved):")
        print("  notes  sampled   anchored (no restring)   middle (no restring)")
        for L, v in physics.items():
            n = max(1, v["sampled"])
            print(f"  {L:5d}  {v['sampled']:7d}   {100 * v['anchored'] / n:5.1f}% "
                  f"({100 * v['anchored_no_regauge'] / n:5.1f}%)        "
                  f"{100 * v['middle'] / n:5.1f}% ({100 * v['middle_no_regauge'] / n:5.1f}%)")
    print(f"\nBest unrelated-sounding pairs: most distinct (A,B) pitch pairs, then longest"
          f" (one per pair of works; solver run on the first {min(a.solve, len(top))}):")
    print(S.format_candidates(top, a.show))
    if a.tabs:
        os.makedirs(a.tabs, exist_ok=True)
        written = 0
        for k, c in enumerate(top[:a.solve], 1):
            if not (c.solved and c.solved.get("anchored")):
                continue
            text = S.render(c, by_ref)
            if text:
                fn = os.path.join(a.tabs, f"{k:03d}-{c.pairs}pairs-{c.length}notes.tab")
                with open(fn, "w") as f:
                    f.write(text + "\n")
                written += 1
        print(f"\n{written} verified shared tabs written to {a.tabs}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"corpora": names, "stats": S.stats_dict(stats),
                       "physics": {str(k): v for k, v in physics.items()},
                       "top": [vars(c) for c in top],
                       "samples": {str(L): [vars(c) for c in cs] for L, cs in samples.items()},
                       "settings": {k: v for k, v in vars(a).items() if k != "func"}},
                      f, indent=1, default=str)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gtrsnipe-research", description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", help=f"corpus root folder (default: ${C.ROOT_ENV})")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("corpus", help="build and inspect melody caches").add_subparsers(
        dest="corpus_cmd", required=True)
    cp.add_parser("list", help="known corpora and whether they are cached").set_defaults(
        func=cmd_corpus_list)
    b = cp.add_parser("build", help="read a corpus into its cache")
    b.add_argument("name", choices=list(C.CORPORA))
    b.add_argument("--out", help="cache file (default: DATA/_cache/NAME.jsonl.gz)")
    b.add_argument("--workers", type=int, help="processes (default: CPUs - 2)")
    b.add_argument("--limit", type=int, help="read only the first N files")
    b.set_defaults(func=cmd_corpus_build)
    i = cp.add_parser("info", help="summary of a cached corpus")
    i.add_argument("name", help="corpus name or cache file")
    i.set_defaults(func=cmd_corpus_info)
    s = cp.add_parser("show", help="print one melody")
    s.add_argument("ref", help="NAME:ID, e.g. essen:deut4659 or essen:deut4659#p2")
    s.set_defaults(func=cmd_corpus_show)

    p = sub.add_parser("profile", help="offset profile of two aligned melodies")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--rhythm", default="strict",
                   help="strict (default), a slop RATIO such as 1.5, or sequence")
    p.add_argument("--subdivide", type=int, default=1,
                   help="let one note stand for up to K notes of the other song")
    p.add_argument("--json", action="store_true", help="one JSON object")
    p.set_defaults(func=cmd_profile)

    fm = sub.add_parser("families", help="tune-family retrieval with each offset measure (R03)")
    fm.add_argument("name", help="a corpus with tune-family labels (mtc-ann, mtc-fs) or cache file")
    fm.add_argument("--grid", type=int, default=64, help="points per melody (default 64)")
    fm.add_argument("--bootstrap", type=int, default=2000, help="resamples for the 95%% intervals")
    fm.add_argument("--seed", type=int, default=20260926)
    fm.add_argument("--queries", type=int, help="use a random sample of N queries")
    fm.add_argument("--no-models", action="store_true", help="skip the logistic pair models")
    fm.add_argument("--json", help="also write the full results here")
    fm.set_defaults(func=cmd_families)

    sc = sub.add_parser("scan", help="find passages of different songs that could share one tab (R04)")
    sc.add_argument("names", nargs="+", help="corpora (or cache files) to scan together")
    sc.add_argument("--unit", choices=["auto", "phrase", "window"], default="auto",
                    help="marked phrases, sliding windows, or phrases where marked (default)")
    sc.add_argument("--window", type=int, default=16, help="window length in notes (default 16)")
    sc.add_argument("--stride", type=int, default=4, help="window step in notes (default 4)")
    sc.add_argument("--min-len", type=int, default=5, help="shortest phrase (default 5 notes)")
    sc.add_argument("--max-len", type=int, default=64, help="longest phrase (default 64)")
    sc.add_argument("--max-richness", type=int, default=6, help="string budget (default 6)")
    sc.add_argument("--keep", type=int, default=300, help="candidates kept (default 300)")
    sc.add_argument("--min-keep-len", type=int, default=8,
                    help="shortest passage kept as a candidate (default 8)")
    sc.add_argument("--solve", type=int, default=25,
                    help="run the homograph solver on the best N candidates (default 25)")
    sc.add_argument("--physics-sample", type=int, default=0,
                    help="also solve N random different-sounding eligible pairs per length")
    sc.add_argument("--show", type=int, default=25, help="candidates listed (default 25)")
    sc.add_argument("--tabs", help="write the verified shared tabs of solved candidates here")
    sc.add_argument("--cross-corpus", action="store_true",
                    help="only pair passages from different corpora")
    sc.add_argument("--named-melodies", action="store_true",
                    help="MIDI corpora: only melodies from a melody-named track (no skyline)")
    sc.add_argument("--seed", type=int, default=20260926)
    sc.add_argument("--json", help="also write stats, candidates and samples here")
    sc.set_defaults(func=cmd_scan)
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        return a.func(a)
    except ValueError as e:
        print(f"gtrsnipe-research: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
