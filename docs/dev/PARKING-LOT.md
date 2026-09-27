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
