# 8. Side discoveries

*Claude's account.*

Things found along the way that weren't the point, some of them useful.

## A tab checker, for free

scottvr started gtrsnipe partly out of frustration with community tab sites, where a song
often has several user-submitted tabs and, often enough, *every one of them is wrong*. Not
wrong by taste:
wrong-wrong, as scottvr put it, meaning no tuning could ever make them right, unless the
tuning changed between notes.

That definition is exactly what the homograph machinery tests. The as-written check asks
whether *any* retuning makes a tab's own fingering play a reference melody. Point it at a
tab and a MIDI of the same passage:

```bash
gtrsnipe --homograph their.tab reference.mid --homograph-rhythm sequence
```

The report sorts the tab into four cases:
- **right**;
- **right in another tuning**: written for drop-D, say, but labelled standard;
- **wrong-wrong**: no tuning fixes it, and the report names the string that carries two
  different intervals;
- **missing or extra notes.**

It was checked on a generated tab with one planted wrong fret. scottvr's reaction: "gotta
love when unexpected free feature use cases just fall from the heavens." It's in the README
now, with follow-ups in the parking lot: list every bad note, tolerate a few missing notes,
and rank many user-submitted versions of one song.

## StegTab

The literature survey listed a "StegTab" as possible prior art, with a guessed description:
hiding bits in redundant fingerings. The guess was wrong. scottvr tracked down the source:
a 2012 WordPress post by Archie Anugrah that hides text in fret numbers. Each letter is the
string's own letter name plus the fret, counted through the alphabet, so no 26-fret neck is
needed. It's a cipher, not music, and not prior art. It has the same shape as the homograph,
though (symbol = string base + fret, as pitch = open + fret), so relabelling the strings
re-keys the message: a homograph in letter space, never taken there.

## Bugs that hid behind other bugs

- **The wheel held 3 of gtrsnipe's 56 modules** (fixed in v0.6.2). The package pattern
  matched only the top level. Editable installs, the README's method, didn't notice, so
  `pip install git+https://…` had been shipping a husk.
- **Every MIDI track was "Acoustic Grand Piano"** (B07). The reader never read track names,
  and it only came to light when the research corpus reader, which reads MIDI directly, kept
  them.
- **A sixteenth-note duration floor** in the MIDI reader (fixed with P01). scottvr traced it
  to early experiments with tab spacing, from before the current tab generator, which spaces
  notes by onset. Nothing depended on it any more.
- **Open strings aren't preferred.** The new `--analyze` (F03) ranked an open-G riff as easy
  in open G as in a barre at fret 3: with default weights, an open string scores no better
  than a fretted note in the sweet spot.
- **Thirty files with Windows line endings**, from the years gtrsnipe was developed on a
  Windows laptop, until the laptop died. Git was never told to normalize them. Fixed with a
  `.gitattributes` on 2026-09-28.

## The weights

`--analyze` and the playability work turned attention back to the mapper's weights. Each
had been added to fix one transcription, just enough to override the knobs before it. That
hand-tuning always eventually worked for a given song. But the Asturias wiki page needs a
long command line to get a playable tab, while Mr Crowley largely works with the defaults.

Discussing why produced a plan, parked for later:
- **Read the weights as exchange rates.** Only their ratios matter, so fix one as "a fret of
  hand travel" and read the others against it. A string switch then costs 1.7 frets of
  travel.
- **Some weights are priorities in disguise.** Asturias's `--let-ring-bonus 210` is worth 70
  frets of travel per ringing string. That isn't a trade-off; it's "ringing always wins".
- **Learn them.** A structured perceptron can learn the weights, or a sample-then-rank loop
  where scottvr judges tabs rather than settings. That yields style profiles (flamenco,
  rockabilly) saved as the `.gtrsnipe` profiles that already exist.

It also produced the idea of **optional notes**: let a player ask for the top three strings
of a barre chord instead of all six, with notes dropped by musical importance.

## The machine

All of this ran on a MacBook Air with about 1 GB of free disk, and a LaCie drive whose exFAT
format gives every file at least 256 KiB, so 12 GB of MIDI corpora occupy about 93 GiB. Scratch
files went to the LaCie, and one full-corpus build was skipped as three hours of machine time.

## scottvr's account

> ✎ the tab-site frustration behind gtrsnipe; finding StegTab; the weights' history from
> the inside.
