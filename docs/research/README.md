# Tab homographs: the research

> **Work in progress.** The research is still underway. The documents here are the versions
> published with v0.6.9. Revisions to them, and new results, will be published together when
> the research has concluded, so this folder and its commit history lag behind the work. The
> code (`gtrsnipe/research/`, the `gtrsnipe-research` command) is current.

gtrsnipe's `--homograph` finds one ordinary, playable tab that plays one song in one tuning
and a different song in another. This folder holds the mathematics, the literature, and the
experiments behind it. How the feature itself works is in
[`../app/DESIGN-homograph.md`](../app/DESIGN-homograph.md).

- **Theory:** [`theory/coupled_transposition_structure.md`](theory/coupled_transposition_structure.md)
  (the offset sequence and its richness) and [`theory/PROOF-alignment.md`](theory/PROOF-alignment.md)
  (distances when the alignment is optimized).
- **Literature:** [`literature/LITERATURE-offsets.md`](literature/LITERATURE-offsets.md).
- **Experiments:** [R03](results/RESULTS-R03-families.md) (tune families),
  [R04](results/RESULTS-R04-scan.md) (how often real songs share a tab) and
  [R05](results/RESULTS-R05-aswritten.md) (published tabs, fingered as written).
