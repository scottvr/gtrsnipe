# Tab homographs: worked examples

Public-domain melodies (plain ABC in C, explicit durations) and the shared tabs
`gtrsnipe --homograph` builds from them. Each `*.report.txt` is the full report,
and each `*.tab` is the tab itself, with every song's tuning key in its header.
Theory: [`docs/dev/DESIGN-homograph.md`](../../docs/dev/DESIGN-homograph.md).

Decode any tab in any key through the ordinary converter, e.g.

```bash
gtrsnipe -i oldmac-twinkle.tab -o a.mid                                          # its own header: A
gtrsnipe -i oldmac-twinkle.tab --tuning-pitches 'E2,A2,Bb2,Bb3,A3,C#4' -o b.mid   # key B
```

| tab | songs | what it shows |
|---|---|---|
| `oldmac-twinkle.tab` | Old MacDonald → Twinkle | An **ordinary STANDARD tab** of Old MacDonald. Retune 4 strings (−3 −2 +3 −4, no re-stringing) and it plays Twinkle in A♭. Rank 4 with `--homograph-octaves` (4 of Twinkle's notes drop an octave; disclosed). Without octaves the rank is 5, and anchored mode would need one string re-gauged (the report flags which and suggests a gauge). |
| `oldmac-twinkle.middle.tab` | Old MacDonald → Twinkle | `--homograph-mode middle`: both tunings are retunes of one 10-46 guitar. Twinkle comes out **exact** (no octave displacement), and no string is re-gauged. |
| `nursery-trio.tab` | Old MacDonald → Twinkle → Mary | **One tab, three songs** (first phrase of each), three tunings, in middle mode with no re-stringing. Anchored to STANDARD it would need 3 strings re-gauged, because Twinkle's intervals span 12 semitones, wider than any string's safe window. |
| `mary-london.tab` | Mary → London Bridge | Rank 6: all six strings, each carrying its own interval. London Bridge's dotted rhythm needs `--homograph-rhythm 2`, and the tab carries Mary's rhythm. |

Also try the re-rhythm aligner on the alphabet song, which sings "L-M-N-O" as
four eighths where Twinkle has two quarter-note Ds:

```bash
gtrsnipe --homograph twinkle.abc abc_song.abc --homograph-subdivide 2
```

It aligns by smearing the repeated Ds, then honestly reports **rank 1: the songs
are identical**. Same tune, so that pair is not a homograph.

Regenerate everything from this directory:

```bash
gtrsnipe --homograph oldmac.abc twinkle.abc@1-12 --homograph-octaves -o oldmac-twinkle.tab -y
gtrsnipe --homograph oldmac.abc twinkle.abc@1-12 --homograph-mode middle -o oldmac-twinkle.middle.tab -y
gtrsnipe --homograph oldmac.abc@1-7 twinkle.abc@1-7 mary.abc@1-7 --homograph-mode middle -o nursery-trio.tab -y
gtrsnipe --homograph mary.abc london_bridge.abc --homograph-rhythm 2 --homograph-mode middle -o mary-london.tab -y
```
