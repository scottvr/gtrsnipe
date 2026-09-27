# Wiki snapshot

A copy of the GitHub wiki (<https://github.com/scottvr/gtrsnipe/wiki>). A GitHub wiki is a
separate git repository (`https://github.com/scottvr/gtrsnipe.wiki.git`), edited through the
web UI and versioned apart from the code. So this folder is a snapshot, and it can drift from
the live wiki.

- **Source:** wiki commit `9301478` (2025-08-09), copied 2026-09-26.
- **File names:** the wiki's page names contain `? # : ( ) "` and a Unicode hyphen, which
  Windows checkouts can't handle, so the copies have plain names. Links between pages still
  use the wiki's names.
- **One page differs from the wiki on purpose:** `4.Example-Asturias_Leyenda.md` was copied
  earlier and later edited here. Commit 99e36d6 renamed the mapper option
  `--count-fret-span-across-neighbors` to `--diagonal-span-penalty`. The live wiki page still
  uses the old name.

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
