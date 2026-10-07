# gtrsnipe documentation

A map of everything under `docs/`, by who it's for.

## Using gtrsnipe

- [`../README.md`](../README.md): installation, the CLI reference, and short examples.
- [`wiki/`](wiki/): a snapshot of the GitHub wiki: the mapper's tunables and worked
  examples (Mr Crowley, the Bach Cello Suite Prelude, Asturias, Barney Miller).
- [`../examples/homograph/`](../examples/homograph/): shared tabs for public-domain tunes.
- [`../examples/aswritten/`](../examples/aswritten/): the wiki's tabs, as used by R05.
- [`../CHANGELOG.md`](../CHANGELOG.md): what changed in each release, and why.

## How gtrsnipe works: [`app/`](app/)

| doc | what it covers |
|---|---|
| [`DESIGN-viterbi-mapper.md`](app/DESIGN-viterbi-mapper.md) | The fretboard mapper as dynamic programming over a trellis (v0.3.0), replacing the greedy per-chord choice (still available with `--optimizer greedy`). |
| [`DESIGN-unified-io.md`](app/DESIGN-unified-io.md) | Renderer × sink × schedule: one pipeline for files and the interactive player; the event-driven transport (v0.5.0), note lengths (v0.6.8). |
| [`DESIGN-homograph.md`](app/DESIGN-homograph.md) | `--homograph`: the eligibility theorem, the solver's modes, string physics, playability, alignment and re-rhythm. |

## The research: [`research/`](research/)

The tab-homograph research: theory and proofs, the literature survey, and the experiments.
Start at [`research/README.md`](research/README.md).

## Process: [`dev/`](dev/)

- [`BACKLOG.md`](dev/BACKLOG.md): the single list of open work, and The Dull Protocol for
  working through it.
- [`PARKING-LOT.md`](dev/PARKING-LOT.md): new ideas waiting for triage.
- [`NOTES-playability.md`](dev/NOTES-playability.md): design notes for the backlog's
  playability items (M01–M07), carried over from the parking lot.
- [`SPEC-tab-rhythm.md`](dev/SPEC-tab-rhythm.md): agreed, not built yet: writing note lengths
  into a tab as a count of dashes (backlog F08).
- [`archive/`](dev/archive/): the v0.3.0-era plans and audit, frozen.

The images in this folder (`gtrsnipe-*.png`) are logo assets.
