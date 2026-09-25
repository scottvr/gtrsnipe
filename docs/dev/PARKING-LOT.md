## gtrsnipe should support aarabitrary tunings easily
**[DONE — v0.5.0]** `--tuning-pitches "A1,E2,A2,D3,F#3,B3"` (low→high) + `--drop-low-string N`.
Custom tunings thread through convert/play/chords; the ASCII-tab parser now decodes in
the configured tuning (was hardcoded standard — a real bug fix, and it enables re-reading a
tab under a different tuning). Also added the inverse **`--solve-tuning`** (melody → tuning
whose all-open tab plays it), the executable form of the copyright reductio.

- we have plenty of useful provided named tunings
- I had an occasion to want a BARITONE_B tuning, but dropping the low B to an A1 (analogous to drop-d tuning where the low three strings play a power chord in open position.) BARITONE_A is avauilable, and drop d is available for 6 strings or bass, but very quickly I thought oh we should just implement a `--drop-low-string`argument so that the user could do this on a 7-string, and in any (supported) tuning. This may still be a good idea for convenience, but immediately I realized that the ability to do --tuning CUSTOM that used the values spcified by maybe a --tuning-pitches where the user can specifiy a runing of num_strings length, low to high, by named pitch class like `--tuning-pitches A1,E2,A2,D3,F#3,B3`, so they'd then be free to name their own tune.

## we should support user prefs/profiles in a .grtrsnipe directory
**[DONE — Unreleased]** Implemented as `--profile`/`--save-args`/`--no-defaults`/
`--config-dir` + auto `defaults`; profile = prepended argv re-parsed. See README
"Config profiles" and `gtrsnipe/arguments.py` (apply_profiles). Custom tunings can
now live in profiles once #1 lands.

- a defaults file will have all option values to use in the absence of an explicit option on the command line.
- individual files of the same format but just stored for convenience and accessible via --profile <name> where <name> corrresponds to the file name within the .gtrsnipe directory (or other specified directory)
- they could store custom tunings in there, too. If we allow multiple --profile arguments (and also comma-separated list of profiles that are applied in order, so we only need to support a single file syntax and not a special one for tunings, they'd pass `--profile my-short-scale-prefs,my_custom_tuning` and both of those files would be read and applied to the current command-line arguments
- applied first, so that then other arguments can override anything from a .gtrsnipe prefs/profile. 
the commands end up very long with lots of commands at times so this would be a time and aggravation saver.
- we could add a --save-args <new_file_name> would would taake the current supplied arguments and write them to a .gtrshnipe/new_file_name file for later re-use.
The file format could be simple ini-ish:
```
argname # for boolean/toggle flags
argname value # for any thaat take options themselves
```

So if I know I always want 
```
--sweet-spot-high 9 --string-switch-penalty 0 --ignore-open 
```

I could create a .gtrsnipe/defaults containing those values, or a file by any other name to load when a --profile is passed.
Here's a spelled out example:
```
# Example gtrsnipe config file:
# .gtrsnipe/spanish
sweet-spot-high = 9
string-switch-penalty = 0
ignore-open 
uweet-spot-low=4 
prefer-open 
unplayable-fret-span=3 
high-fret-penalty=50 
dedupe 
fretted-open-penalty = 10 
movement-penalty =20 
let-ring-bonus  = 210 
diagonal-span-penalty 
no-articulations
```
Make sense?

## midi player sensible defaults
We might want to respect midi instruments that may be specified in a .mid file. For display/comment perhaps and for when the audio player is used. Similarly for midi channels if we're sending out to a midi port. track/channel/inst, what else?
