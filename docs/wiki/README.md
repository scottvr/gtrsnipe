# Wiki snapshot

A copy of the GitHub wiki (<https://github.com/scottvr/gtrsnipe/wiki>). A GitHub wiki is a
separate git repository (`https://github.com/scottvr/gtrsnipe.wiki.git`), edited through the
web UI and versioned apart from the code. So this folder is a snapshot, and it can drift from
the live wiki.

- **Source:** wiki commit `9301478` (2025-08-09), copied 2026-09-26.
- **Edited here since:** on 2026-09-28 the pages were brought up to date with the code of
  v0.6.10 (the docs audit, items WK-1 to WK-27). None of these edits
  are on the live wiki yet.
- **File names:** the wiki's page names contain `? # : ( ) "` and a Unicode hyphen, which
  Windows checkouts can't handle, so the copies have plain names. Links between pages still
  use the wiki's names.

## Versions

The example pages (2 to 5), the FAQ and the v0.2.0 log were written for gtrsnipe v0.2, whose
mapper chose each chord's fingering greedily. Since v0.3.0 the default mapper optimizes the
whole piece, so several tabs on those pages come out differently today; `--optimizer greedy`
reproduces them. Each of those pages now starts with a note saying so, and short notes mark
commands and claims that have changed. Their narrative and their tabs are unchanged.

Pages 0 and 1 were rewritten: page 0 has a page index and a summary of what's new since v0.3,
and page 1 is a reference rebuilt from `gtrsnipe --help` and `gtrsnipe/arguments.py`.

## Differences from the live wiki

- Every page except Home and the footer differs, as described above.
- The live wiki's Asturias page (4) still uses `--count-fret-span-across-neighbors`, which
  commit 99e36d6 renamed to `--diagonal-span-penalty`. gtrsnipe now rejects the old name, so
  that page's later commands fail as written. The copy here uses the new name.

| file here | wiki page |
|---|---|
| `Home.md` | Home |
| `0.GTRSnipe.md` | 0. GTRSnipe (aka "guttersnipe") |
| `1.FretboardMapper-Algorithm-Configuration-and-Tunables.md` | 1. FretboardMapper Algorithm Configuration and Tunables |
| `2.Example-Mr-Crowley-organ-intro.md` | 2. Example ‐ Mr Crowley organ intro |
| `3.Example-Bach-Cello-Suite-1-Prelude.md` | 3. Example ‐ Bach Cello Suite #1 (Prelude) |
| `4.Example-Asturias_Leyenda.md` | 4. Example Asturias (Leyenda), aka Prelude |
| `5.Example-Barney-Miller-Theme-audio-to-tab.md` | gtrsnipe's first real success transcribing AUDIO to Tablature! Barney Miller Theme |
| `Tablature-Editors-FAQ.md` | Tablature Editors already exist and some can auto‐generate from MIDI; how is gtrsnipe any better? |
| `v0.2.0.md` | v0.2.0 |
| `_Footer.md` | (footer) |
