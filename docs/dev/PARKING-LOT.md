# Parking lot

Quick capture for new ideas. Write one or two lines each; there's no need to think them
through or start them. Nothing here is scheduled.

At each triage, every entry either moves into [`BACKLOG.md`](BACKLOG.md), the single list
of open work with a plan, or is declined, and is removed from this file. (This is part of
The Dull Protocol, described at the top of the backlog.)

Earlier entries (custom tunings, profiles, homographs, MIDI player defaults) were
triaged on 2026-09-26. The finished ones are in the CHANGELOG, the open ones are in the
backlog, and the original notes are in git history.

## Ideas

- **Bug: `MidiReader` drops MIDI track names** (found during R01, 2026-09-26). The mido path
  never reads `track_name` meta events (`temp_track_name` stays `None`), so every track is
  "Acoustic Grand Piano"; only the py-midi fallback keeps names. Fixing it changes tab titles
  ("Title (Melody)"), so re-bless any golden cases. The research corpus reader uses mido
  directly and is unaffected.
- **R04 follow-ups** (2026-09-26):
  - Scan with re-rhythm (a rhythm slop ratio, `--homograph-subdivide`); today only identical or
    proportional rhythms meet.
  - Rank candidates by playability, since the solver happily reaches fret 24 on the low
    strings. Proposed design (scottvr, 2026-09-26): a `--homograph-max-discomfort` flag (or
    `--homograph-min-playability`) built on the mapper's existing Viterbi score, which is
    already on `Solution.playability`. It would report the score per note, reject solutions
    over the limit so the solver tries its next candidate, and let `scan` rank and filter by
    it. Calibrate it against the tab gtrsnipe writes for song A alone ("1.5 = at most 1.5x
    as awkward per note"); check the score's sign and scale first. Quick win meanwhile:
    `scan`'s `solve()` should pass `--max-fret` through, which `--homograph` already takes.
  - Build and scan LMD-full (178k files, about 3 h to cache).
- **R03 follow-up**: richness under its *own* optimal warping (a minimum-label path) as the fair
  similarity test; see RESULTS-R03 "Limits".
- **R06/R07 follow-up: a targeted literature search** for the stutter-invariance principle in
  PROOF-alignment.md: warping-minimized, stutter-invariant, subadditive statistics are
  pseudometrics. Start from the discrete Fréchet distance (Eiter & Mannila 1994; Alt & Godau
  1995), whose triangle-inequality proof is the same path composition, and the elastic
  distances built to be metrics (ERP, TWED, Move-Split-Merge). Needed before any novelty
  claim about the general statement. The citation checklist and the questions to answer are in
  PROOF-alignment.md, "Citations to verify" (scottvr starting a verification pass 2026-09-27).
