# gtrsnipe 
(pronounced "guttersnipe")

Convert to and from .mid, .abc, .vex, and .tab files. 

### What?

**gtrsnipe** will convert MIDI (from a .mid file) into text-based transcriptions (ASCII tab, VexTab, and ABC notation) arranged for 6-string guitar.

**gtrsnipe** can also convert these text-based notations into a playable MIDI file from a .vex, .abc, or .tab file. Note that since standard ASCII .tab does not encode rhythmic information, **gtrsnipe** tries to infer an approximation of this based on the spacing between notes (and the number of `-` characters between fretted notes) and since tabs found in the wild are all over the place in this respect, YMMV. 

Note that to strike a balance between readability and compactness, **gtrsnipe** uses a logarithmic spacing algorithm when generating ASCII tabs from MIDI to try and encode as much of this information as possible given the format, so tabs that were originally created by **gtrsnipe** will often fare better in the final playback of a generated midi than ones posted to usenet in the 1990's, but of course if it was generated with gtrsnipe, you already had a mid, vex, or abc of the song which already had rhythmic information to start with so re-midifying from a gtrsnipe tab is kinda pointless, isn't it? 

By default **gtrsnipe** will try to infer hammer-on/pull-off performance technique articulations based on the timing of the notes. You can disable this (for straight-picking transcriptions) with `--no-articulations`. Additionally, there is a `--single-string` option for transcriptions that might be best represented on one string with taps/hammer-ons/pull-offs. Best for pieces/segments you know should be played in this manner.

**gtrsnipe** tries to intelligently find the best neck and fingering positions using a note to fretboard mapper and a scoring algorithm that is unavoidably shaped by my *subjective* opinions and skills as a player but it  does its best to avoid *objectively* impossible fingerings.

The `--nudge` option exists because MIDI track start times can sometimes also be all over the place and is designed to help you make your ascii TAB more visually appealing, though not necessarily accurate in terms of how many "rest" measures there may be before the transcription begins. See example usage below.

The parameter `--max-line-wdith` exists primarily to constrain a tab staff to a certain width suitable for printing on your medium of choice. The default is `40` which ensures a measure fits on standard portrait-orientation 8.5x11" paper, but you are free to make it wider for your computer display or wide-format printing, smaller fonts, etc.

## Installation

### Prerequisites

You must have a working Python programming language environment installed (from python.org or your system's software package manager) as well as `git` (from git-scm.com or your system's software package manager.)

### Procedure

```
git clone https://github.com/scottvr/gtrsnipe
cd gtrsnipe
python -mvenv .venv
```

on Windows:

```
.venv\Scripts\activate
```

or in bash:

```
. .venv/bin/activate
```

Then, 

```
pip install .
```


## Basic Usage Help

The installation process makes gtrsnipe available as a command within your venv.

```
usage: gtrsnipe [-h] [--nudge NUDGE] [-y] [--track TRACK]
                [--constrain-pitch] [--pitch-mode {drop,normalize}]
                [--transpose TRANSPOSE] [--no-articulations] [--staccato]
                [--max-line-width MAX_LINE_WIDTH] [--bass]
                [--num-strings {4,5,6,7}] [--single-string {1,2,3,4,5,6}]
                [--debug] [--list-tunings] [--show-tuning TUNING_NAME]
                [--tuning {STANDARD, E_FLAT, DROP_D, ... ]
                [--max-fret MAX_FRET]
                input_file output_file

Convert music files between binary MIDI .mid and ASCII .tab .vex, and .abc notation formats, in any direction.

positional arguments:
  input_file          Path to the input music file
  output_file         Path to save the output music file

options:
  -h, --help            show this help message and exit
  --nudge NUDGE         An integer to shift the transcription's start time to
                        the right. Each unit corresponds to roughly a 16th
                        note.
  -y, --yes             Automatically overwrite the output file if it already exists.
  --track TRACK         The track number (1-based) to select from a multi-
                        track MIDI file. If not set, all tracks are processed.
                        For a multitrack midi, you will want to select a
                        single instrument track to transcribe.
  --analyze             Analyze the input MIDI file to find its pitch range
                        and suggest suitable tunings, then exit.  
  --constrain-pitch     Constrain notes to the playable range of the tuning
                        specified by --tuning.  
  --pitch-mode {drop,normalize}
                        Used with --constrain-pitch. ‘drop’ (default) discards
                        out-of-range notes; ‘normalize’ transposes them by
                        octaves until they fit.  

  --transpose TRANSPOSE
                        Transpose the music up or down by N semitones (e.g., 2
                        for up, -3 for down).
  --no-articulations    Transcribe with no legato, taps, hammer-ons, pull-
                        offs, etc.
  --staccato            Do not extend note durations to the start of the next note for a sustained feel,
                        instead giving each note an 1/8 note duration. When converting *from* ASCII tab.
  --max-line-width MAX_LINE_WIDTH
                        Max number of vertical columns per line of ASCII tab.
                        (default: 40)
  --bass                Enable bass mode. Automatically uses bass tuning and a
                        4-string staff.
  --num-strings {4,5,6,7}
                        Force the number of strings on the tab staff (4, 5, 6,
                        or 7). Defaults to 4 for bass and 6 for guitar.
  --single-string {1,2,3,4,5,6}
                      Force all notes onto a single string (1-6, high e to low E). Ideal for transcribing legato/tapping runs.
  --debug             Enable detailed debug logging messages.

Tuning Information:
  --list-tunings        List all available tuning names and exit.
  --show-tuning TUNING_NAME
                        Show the notes for a specific tuning and exit.

```

### Current Supported Tunings

```
$ gtrsnipe  --list-tunings                                                   
Available Tunings:
- STANDARD              : E4 B3 G3 D3 A2 E2
- E_FLAT                : Eb4 Bb3 Gb3 Db3 Ab2 Eb2
- DROP_D                : E4 B3 G3 D3 A2 D2
- D_STANDARD            : D4 A3 F3 C3 G2 D2
- DROP_C                : D4 A3 F3 C3 G2 C2
- DROP_B                : C#4 F#3 B2 E2 B1
- OPEN_G                : D4 B3 G3 D3 G2 D2
- OPEN_E                : E4 B3 G#3 E3 B2 E2
- DADGAD                : D4 A3 G3 D3 A2 D2
- OPEN_D                : D4 A3 F#3 D3 A2 D2
- OPEN_C6               : E4 C4 G3 C3 A2 C2
- BASS_STANDARD         : G2 D2 A1 E1
- BASS_DROP_D           : G2 D2 A1 D1
- BASS_E_FLAT           : Gb2 Db2 Ab1 Eb1
- SEVEN_STRING_STANDARD : E4 B3 G3 D3 A2 E2 B1
- SEVEN_STRING_DROP_A   : E4 B3 G3 D3 A2 E2 A1
- BARITONE_B            : B3 F#3 D3 A2 E2 B1
- BARITONE_A            : A3 E3 C3 G2 D2 A1
- BARITONE_C            : C4 G3 Eb3 Bb2 F2 C2
```

### Usage Examples  

Transcribing this organ intro for my classical guitar, where the "sweet spot" is lower on the neck:

```
$ gtrsnipe MrCrowleyOrganIntro.mid mrcrowley-organ.tab --track 5 --sweet-spot-high 8 --max-line-width 120
Converting 'MrCrowleyOrganIntro.mid' (mid) to 'mrcrowley-organ.tab' (tab)...
--- Selecting track 5 of 7 ---
--- Chord-Aware Mapper initialized. ---
Successfully saved to mrcrowley-organ.tab
```

That command extracts track 5 (the organ track) from a multi-track MIDI file found on the Internet, prefers frets between open and 8th when mapping notes to frets, and outputs the measures up to 120 characters per line. Here's what the output looks like:

```
// Title: MrCrowley-OrganIntro
// Tempo: 120.0 BPM
// Time: 4/4
// Tuning: STANDARD

e|-------------------|-----------------------|--1----------------|--3--------------------|--5----------------|
B|--6----------------|--5--------------------|--1----------------|--5--------------1---p0|--5----------------|
G|--7----------------|--5--------------------|--2-----0---h2----4|--5--------------------|--5-----4---h5----7|
D|--7---------------5|--7--------------7---p5|--3----------------|--5-----5--------------|--7----------------|
A|--5-----7---h8-----|--7-----7--------------|--3----------------|--3---------3----------|--7----------------|
E|-------------------|--5---------5----------|--1----------------|-----------------------|--5----------------|

e|--7-------------|-------------1--|--3----1----0----1|--5-------------|----------------|-------------------|
B|--8-------------|-------------1--|--3----1----0----1|--6-------------|--5-------------|--6----------------|
G|--9-------------|--5-----7-------|------------------|--7-------------|--6-------------|--7----------------|
D|--9----9--------|--7-----8----3--|--5----3----2----3|--7-------------|--------3---p2--|--7---------------5|
A|--7---------7---|----------------|------------------|----------------|----------------|--5-----7---h8-----|
E|----------------|--5-----6----1--|--3----1----0----1|--5-------------|----------------|-------------------|

e|-----------------------|--1----------------|--3--------------------|--5----------------|--7-------------|
B|--5--------------------|--1----------------|--5--------------1---p0|--5----------------|--8-------------|
G|--5--------------------|--2-----0---h2----4|--5--------------------|--5-----4---h5----7|--9-------------|
D|--7--------------7---p5|--3----------------|--5-----5--------------|--7----------------|--9----9--------|
A|--7-----7--------------|--3----------------|--3---------3----------|--7----------------|--7---------7---|
E|--5---------5----------|--1----------------|-----------------------|--5----------------|----------------|

e|-------------1--|--3----1----0----1|--5-------------|----------------|
B|-------------1--|--3----1----0----1|--6-------------|--5-------------|
G|--5-----7-------|------------------|--7-------------|--6-------------|
D|--7-----8----3--|--5----3----2----3|--7-------------|----------------|
A|----------------|------------------|----------------|----------------|
E|--5-----6----1--|--3----1----0----1|--5-------------|----------------|
```

When transcribing a bass part, pass the proper tuning and (optionally) the number of strings. Without these arguments, transcribing a bass part will work, but the mapper will transpose to guitar notes and display on six strings. You can simply pass the `--bass` option as a shortcut for 4-strings, standard bass tuning. Passing a --tuning BASS_* tuning will by default render your tab with four strings, but you can override this with `--num-strings 5`, for example.

```
$ gtrsnipe SmellsLikeTeenSpirit.mid --track 6 teenspirit-bass.tab --no-articulations --nudge 14 --tuning BASS_E_FLAT
Converting 'SmellsLikeTeenSpirit.mid' (mid) to 'teenspirit-bass.tab' (tab)...
--- Selecting track 6 of 11 ---
--- Nudging all events forward by 3.5 beats ---
--- Chord-Aware Mapper initialized. ---
Successfully saved to teenspirit-bass.tab

$ cat teenspirit-bass.tab
// Title: SmellsLikeTeenSpirit
// Tempo: 120.0 BPM
// Time: 4/4
// Tuning (High to Low): Gb2 Db2 Ab1 Eb1

G|----------------|----------------|----------------|----------------|----------------|----------------|
D|----------------|----------------|----------------|----------------|----------------|----------------|
A|----------------|----------------|----------------|----------------|----------------|----------------|
E|----------------|----------------|----------------|----------------|----------------|----------------|

G|---------------------------------|---------------------------------|---------------------------------|
D|---------------------------------|---------------------------------|---------------------------------|
A|------------------------2---2----|------------------------5---5----|------------------------2---2----|
E|--2----2--2----2--2--2----------2|--5----5--5----5--5--5----------5|--2----2--2----2--2--2----------2|

G|---------------------------------|---------------------------------|---------------------------------|
D|---------------------------------|---------------------------------|---------------------------------|
A|------------------------5---5----|------------------------2---2----|------------------------5---5----|
E|--5----5--5----5--5--5----------5|--2----2--2----2--2--2----------2|--5----5--5----5--5--5----------5|

G|---------------------------------|---------------------------------|-------------------------------|
D|---------------------------------|---------------------------------|-------------------------------|
A|------------------------2---2----|------------------------5---5----|------------------2---2---2---2|
E|--2----2--2----2--2--2----------2|--5----5--5----5--5--5----------5|--2---2---2---2----------------|
```

## Advanced Usage: Fretboard Mapper Tuning

The following options can be used to tweak the fretboard positioning/fingering algorithm:

```
Mapper Tuning/Configuration (Advanced):
  --tuning {STANDARD,E_FLAT,DROP_D,OPEN_G,BASS_STANDARD,BASS_DROP_D,BASS_E_FLAT,SEVEN_STRING_STANDARD,SEVEN_STRING_DROP_A,BARITONE_B,BARITONE_A,OPEN_C,OPEN_C6}
                        Specify the guitar tuning (default: STANDARD).
  --max-fret MAX_FRET   Maximum fret number on the virtual guitar neck
                        (default: 24).
  --fret-span-penalty FRET_SPAN_PENALTY
                        Penalty for wide fret stretches (default: 100.0).
  --movement-penalty MOVEMENT_PENALTY
                        Penalty for hand movement between chords (default:
                        3.0).
  --string-switch-penalty STRING_SWITCH_PENALTY
                        Penalty for switching strings (default: 5.0).
  --high-fret-penalty HIGH_FRET_PENALTY
                        Penalty for playing high on the neck (default: 5).
  --low-string-high-fret-multiplier LOW_STRING_HIGH_FRET_MULTIPLIER
                        Multiplier penalty for playing high on the neck on low
                        strings (default: 10).
  --unplayable-fret-span UNPLAYABLE_FRET_SPAN
                        Fret span considered unplayable (default: 4).
  --sweet-spot-bonus SWEET_SPOT_BONUS
                        Bonus for playing in the ideal lower fret range.
  --sweet-spot-low SWEET_SPOT_LOW
                        Lowest fret of the "sweet spot" (default 0 - open)
  --sweet-spot-high SWEET_SPOT_HIGH
                        Highest fret of the "sweet spot" (default 12)
  --ignore-open         Don't consider open when calculating shape score.
  --dedupe                  Enable de-duplication of notes with the same pitch
                              within a chord (drops duplicates).  
  --quantization-resolution {0.0625,0.125,0.25,0.5,1.0}
                              Quantization resolution for grouping simultaneous
                              notes (default: 0.125).  
  --prefer-open             Prefer open strings over fretted equivalents.
  --fretted-open-penalty F
                              Penalty for choosing a fretted note when an open
                              string is available (default: 20.0).  
  --legato-time-threshold LEGATO_TIME_THRESHOLD
                        Max time in beats between notes for a legato phrase
                        (For h/p when infer articulation is enabled (default)) (default: 0.5).
  --tapping-run-threshold TAPPING_RUN_THRESHOLD
                        Min number of notes in a run to be considered for
                        tapping (when infer articulation is enabled (default)) (default: 2).    
```

`--debug` can be used to show the scoring calculations to gain understanding of how your tweaks affect the results.

### Effects of mapper tunables

`--ignore-open` can make a surprising amount of difference without having to tweak scoring weights.
Compare the first few measures of MrCrowley from earlier:

Normal transcription:
```
e|-------------------|-----------------------|--1----------------|--3--------------------|--5----------------|
B|--6----------------|--5--------------------|--1----------------|--5--------------1---p0|--5----------------|
G|--7----------------|--5--------------------|--2-----0---h2----4|--5--------------------|--5-----4---h5----7|
D|--7---------------5|--7--------------7---p5|--3----------------|--5-----5--------------|--7----------------|
A|--5-----7---h8-----|--7-----7--------------|--3----------------|--3---------3----------|--7----------------|
E|-------------------|--5---------5----------|--1----------------|-----------------------|--5----------------|
```

with `--ignore-open`:
```
e|--1----------------|--0--------------------|--1----------------|--3--------------------|--5----------------|
B|--3----------------|--1--------------------|--1----------------|--5--------------1---p0|--5----------------|
G|--2----------------|--2--------------2---p0|--2-----0---h2----4|--5--------------------|--5-----4---h5----7|
D|--0-----2---h3----5|--2-----2--------------|--3----------------|--5-----5--------------|--7----------------|
A|-------------------|--0---------0----------|--3----------------|--3---------3----------|--7----------------|
E|-------------------|-----------------------|--1----------------|-----------------------|--5----------------|
```


If you know you want to play a piece in a certain position, tweak the "sweet spot". For example is a  transcription of a Bach Cello piece, Suite No. 1 in G major - BWV 1007 (Prelude), check out this section:

```
e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--------4--6--7--4--------------4--6--7--4--1---|
A|--0--4--------------4--2--0--4-----------------4|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|------------------------------------------------|
A|--3--6--3--6--9--6--9--6--3--6--3--6--9--6--9--6|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|------------------------------------------------|
A|--7--6--4--7--6--7--9--6--7--6--4--2--0---------|
E|-----------------------------------------4--2--0|
```

The default scoring doesn't work perfectly for this piece, imo. To my ears and hands, there is too much playing on a single string, and on my classical guitar, those 3-6-9 fret spans are impossible for me to play comfortably. So, let's remove the penalty for switching strings and see what happens to that `3-6-3-6-9 ...` measure:

```
e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--------------4-----4-----------------4-----4---|
A|-----6-----6-----6-----6-----6-----6-----6-----6|
E|--8-----8-----------------8-----8---------------|
```

OK, that's better; a little easier to fret, but it is bit high up on the neck for my taste. Let's try tweaking the default "sweet-spot" from the first 12 frets, to just the first four frets plus the open string.

with `--sweet-spot-low 0`, `--sweet-spot-high 4`, and `--string-switch-penalty 0`,
the measure comes out exactly how I would have transcribed it manually:
```
e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|-----1-----1--4--1--4--1-----1-----1--4--1--4--1|
A|--3-----3-----------------3-----3---------------|
E|------------------------------------------------|
```

Here is the full command-line use to get this full transcription:
```
$ gtrsnipe csx.mid csx.tab --string-switch-penalty 0 --no-articulations --sweet-spot-high 4 -y 
$ cat ./csx.tab

e|------------------------------------------------|
B|------------------------------------------------|
G|--------1-----1-----1-----------1-----1-----1---|
D|-----------4-----------------------4------------|
A|-----2-----------2-----2-----2-----------2-----2|
E|--0-----------------------0---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------2--1--2-----2-----------2--1--2-----2---|
D|------------------------------------------------|
A|-----4-----------4-----4-----4-----------4-----4|
E|--0-----------------------0---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------2--1--2-----2-----------2--1--2-----2---|
D|-----1-----------1-----1-----1-----------1-----1|
A|------------------------------------------------|
E|--0-----------------------0---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------1-----1-----1-----------1-----1-----1---|
D|-----2-----4-----2-----2-----2-----4-----2-----1|
A|------------------------------------------------|
E|--0-----------------------0---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------1-----1---------------------------------|
D|-----------4-----2--1--2-----2--1--2------------|
A|-----4--------------------4--------------2--1---|
E|--0-----------------------------------4--------4|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|-----2--4--2--4--2--4--2-----2--4--2--4--2--4--2|
A|--1-----------------------1---------------------|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------4--3--4---------------------------------|
D|--1--4-----------4--2--4--1--4--2--4-----1------|
A|--------------------------------------2-----4--2|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--------2--1--2-----2-----------2--1--2-----2---|
A|--4-----------------------4---------------------|
E|-----4-----------4-----4-----4-----------4-----4|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----------------------------------4--3--1------|
D|--------------------------2--1--------------4--2|
A|--4--1--2--4--2--1--------------4---------------|
E|--------------------4--2------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----------4-----4------------------------------|
D|--1-----------4-----1--4--------1--4--2--1------|
A|-----4--2-----------------2--4--------------4--2|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------------------------1---------------------|
D|--3-----0-----0-----3-----------0-----0-----3---|
A|-----2-----4-----2-----2-----2-----4-----2-----2|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----------1--2--------------------1--2---------|
D|--------4--------4--------------4--------4--1---|
A|--0--4--------------4--2--0--4-----------------4|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|-----1-----1--4--1--4--1-----1-----1--4--1--4--1|
A|--3-----3-----------------3-----3---------------|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--2--1-----2--1--2--4--1--2--1------------------|
A|--------4-----------------------4--2--0---------|
E|-----------------------------------------4--2--0|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--1-----------------------1---------------------|
A|-----0--2--0--2--0--2--0-----0--2--0--2--0--2--0|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--------0-----0-----0-----------0-----0-----0---|
A|-----------4-----------------------4------------|
E|--0--4-----------4-----4--0--4-----------4-----4|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|------------------------------------------------|
A|-----0--4--2--4--0--4--0-----0--4--2--4--0--4--0|
E|--0-----------------------0---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------2--1--2-----2-----------2--1--2-----2---|
D|-----1-----------1-----1-----1-----------1-----1|
A|------------------------------------------------|
E|--0-----------------------0---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------1-----1---------------------------------|
D|-----------4-----2--1--------------------1------|
A|-----2-----------------4--2--0--------------4--2|
E|--0-----------------------------4--2--0---------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|-----------1--2-----1--2-----------1--2-----1--2|
A|--1-----4--------4--------1-----4--------4------|
E|-----2-----------------------2------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--------------1--------1--------------1--------1|
A|--0-----2--4-----2--4-----0-----2--4-----2--4---|
E|-----2-----------------------2------------------|

e|--------------------------------------------|
B|--------------------------------------------|
G|-----------------3--4-----------------------|
D|-----------1--4-------------------------1--2|
A|--0-----2----------------------0--2--4------|
E|-----2-------------------2--4---------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----------------------1--2--------------1--2--4|
D|--4--1--------1--2--4--------4--1--2--4---------|
A|--------2--4------------------------------------|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--5--4--3--4--4--2--1--2--2---------------------|
D|-----------------------------4--1---------------|
A|-----------------------------------4--2--------0|
E|-----------------------------------------2--4---|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----------------1--2-----1---------------------|
D|-----------1--4--------4-----2------------------|
A|--2-----2-----------------------2--0------------|
E|-----2--------------------------------4--0--2--4|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------------------1-----3--1------------------|
D|--------------2--4-----2--------4--5--5--4--3--4|
A|--2--------2------------------------------------|
E|-----0--4---------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----------------------------------------3--4--3|
D|--4--2--1--2--2--------------------2--4---------|
A|-----------------4--1--------1--4---------------|
E|-----------------------4--2---------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--4---------------------------------------------|
D|-----4--1-----1--4-----1--------------------1---|
A|-----------4--------2--------2--1--------------4|
E|--------------------------2--------4--2--0------|

e|----------------------------------------------|
B|----------------------------------------------|
G|------2--1-----------------2--1---------------|
D|------------4--2--1--------------4--2--1------|
A|--2------------------4--2-----------------4--2|
E|----------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|-----1------------------------------------------|
D|--------4--2--1--------------4--2--1------------|
A|--0--------------4--2--0--------------4--2--0---|
E|--------------------------4--------------------4|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|-----2--1-----1--4-----4-----4--1--4--2--4-----4|
A|-----------4--------2-----4-----------------4---|
E|--2---------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--1--4-----4--2--4-----4--1--4-----4--2--4-----4|
A|--------2-----------4-----------2-----------4---|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------------------------------------1---------|
D|--1--4-----4-----4--1--4--2--4--4--4-----4-----4|
A|--------2-----4-----------------------------2---|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------1-----2-----------1-----2-----4-----1---|
D|--4--4-----4-----4-----4-----4-----4-----4-----4|
A|--------------------2---------------------------|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--2-----1-----2-----------1-----------1---------|
D|-----4-----4-----4--4--4-----4--4--4-----4--2--4|
A|------------------------------------------------|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|------------------------------------------------|
D|--4--4--2--4--4--4--1--4--2--4--1--4--2--4-----4|
A|--------------------------------------------4---|
E|------------------------------------------------|

e|------------------------------------------------|
B|------------------------------------------------|
G|--------------------------------------------0---|
D|--1--4--------0-----1-----2-----3-----4---------|
A|--------2--4-----2-----2-----2-----2-----2-----2|
E|------------------------------------------------|

e|------------------------------------------------|
B|--------------------------1-----2-----3-----4---|
G|--1-----2-----3-----4---------------------------|
D|------------------------------------------------|
A|-----2-----2-----2-----2-----2-----2-----2-----2|
E|------------------------------------------------|

e|--0-----------0-----0-----0-----------0-----0---|
B|------------------------------------------------|
G|-----1-----1-----1-----1-----1-----1-----1-----1|
D|------------------------------------------------|
A|--------2-----------------------2---------------|
E|------------------------------------------------|

e|--0---------------------------------------------|
B|--------------5-----5-----5-----------5-----5---|
G|------------------------------------------------|
D|-----4-----4-----4-----4-----4-----4-----4-----4|
A|--------2-----------------------2---------------|
E|------------------------------------------------|

e|------------------------------------------------|
B|--4-----------4-----4-----4-----------4-----4---|
G|-----2-----2-----2-----2-----2-----2-----2-----2|
D|------------------------------------------------|
A|--------2-----------------------2---------------|
E|------------------------------------------------|

e|--0-------------|
B|----------------|
G|----------------|
D|----------------|
A|----------------|
E|----------------|
```
