# Tab homographs: worked examples

Public-domain melodies (plain ABC in C, explicit durations) and the shared tabs
`gtrsnipe --homograph` builds from them. Each `*.report.txt` is the full report,
and each `*.tab` is the tab itself, with every song's tuning key in its header.
Theory: [`docs/app/DESIGN-homograph.md`](../../docs/app/DESIGN-homograph.md).

Decode any tab in any key through the ordinary converter, e.g.

```bash
gtrsnipe -i oldmac-twinkle.tab -o a.mid                                          # its own header: A
gtrsnipe -i oldmac-twinkle.tab --tuning-pitches 'E2,A2,Bb2,Bb3,A3,C#4' -o b.mid   # key B
```

| tab | songs | playability | what it shows |
|---|---|---|---|
| `oldmac-twinkle.tab` | Old MacDonald → Twinkle | 4.4, frets 0–10 | An **ordinary STANDARD tab** of Old MacDonald. Retune 4 strings (−3 −2 +3 −4, no re-stringing) and it plays Twinkle in A♭. Richness 4 with `--homograph-octaves` (4 of Twinkle's notes drop an octave; disclosed). Without octaves the richness is 5, and anchored mode would need one string re-gauged (the report flags which and suggests a gauge). |
| `oldmac-twinkle.middle.tab` | Old MacDonald → Twinkle | 30.8, frets 0–15 | `--homograph-mode middle`: both tunings are retunes of one 10-46 guitar. Twinkle comes out **exact** (no octave displacement), and no string is re-gauged. |
| `nursery-trio.tab` | Old MacDonald → Twinkle → Mary | 61.7, frets 1–18 | **One tab, three songs** (first phrase of each), three tunings, in middle mode with no re-stringing. Anchored to STANDARD it would need 3 strings re-gauged, because Twinkle's intervals span 12 semitones, wider than any string's safe window. |
| `mary-london.tab` | Mary → London Bridge | 92.7, frets 1–22 | Richness 6: all six strings, each carrying its own interval. London Bridge's dotted rhythm needs `--homograph-rhythm 2`, and the tab carries Mary's rhythm. |

*Playability* is the report's discomfort, how many mapper points per note the shared
tab scores below the first song's own best tab in the same tuning (0 = no comfort lost),
and the frets the tab uses. See [`DESIGN-homograph.md`](../../docs/app/DESIGN-homograph.md)
§3, "Playability". The first tab costs little comfort; the others are awkward (a
discomfort of 30 is roughly an extra 10-fret leap per note).

Also try the re-rhythm aligner on the alphabet song, which sings "L-M-N-O" as
four eighths where Twinkle has two quarter-note Ds:

```bash
gtrsnipe --homograph twinkle.abc abc_song.abc --homograph-subdivide 2
```

It aligns by smearing the repeated Ds, then honestly reports **richness 1: the songs
are identical**. Same tune, so that pair is not a homograph.

Regenerate everything from this directory:

```bash
gtrsnipe --homograph oldmac.abc twinkle.abc@1-12 --homograph-octaves -o oldmac-twinkle.tab -y > oldmac-twinkle.report.txt
gtrsnipe --homograph oldmac.abc twinkle.abc@1-12 --homograph-mode middle -o oldmac-twinkle.middle.tab -y > oldmac-twinkle.middle.report.txt
gtrsnipe --homograph oldmac.abc@1-7 twinkle.abc@1-7 mary.abc@1-7 --homograph-mode middle -o nursery-trio.tab -y > nursery-trio.report.txt
gtrsnipe --homograph mary.abc london_bridge.abc --homograph-rhythm 2 --homograph-mode middle -o mary-london.tab -y > mary-london.report.txt
```
