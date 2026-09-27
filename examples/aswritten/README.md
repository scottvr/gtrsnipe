# Tabs for the as-written test (R05)

Tabs extracted from the wiki (snapshot in [`docs/wiki/`](../../docs/wiki/)), all made by earlier
gtrsnipe versions from public-domain music. Each file has a `// Tuning:` header (STANDARD).

| file | source | notes |
|---|---|---|
| `bach-prelude-full.tab` | Bach, Cello Suite No. 1, Prelude: the wiki's full transcription (42 systems) | 654 notes on 6 strings |
| `bach-prelude-measure-default.tab` | one measure, default mapper scoring | every string holds a single pitch |
| `bach-prelude-measure-manual.tab` | the same measure, "how I would have transcribed it manually" | two pitches share a string |
| `asturias-v1.tab` … `asturias-v6.tab` | Albéniz, *Asturias (Leyenda)*: the wiki's six successive transcriptions, from the first autotranscription (v1, with doubled unisons) to v6, the fingering scottvr plays by ear | 29–45 notes |

Run the test:

```bash
gtrsnipe-research aswritten examples/aswritten/*.tab --corpora essen mtc-fs nottingham pop909 lakh-clean
```

Results: [`docs/dev/RESULTS-R05-aswritten.md`](../../docs/dev/RESULTS-R05-aswritten.md).
