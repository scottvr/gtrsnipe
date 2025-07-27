# gtrsnipe 
(pronounced "guttersnipe")

Convert to and from .mid, .abc, .vex, and .tab files. 

### What?

**gtrsnipe** will convert MIDI (from a .mid file) into text-based transcriptions (ASCII tab, VexTab, and ABC notation) arranged for 6-string guitar.

**gtrsnipe** can also convert these text-based notations into a playable MIDI file from a .vex, .abc, or .tab file. Note that since standard ASCII .tab does not encode rhythmic information, **gtrsnipe** tries to infer an approximation of this based on the spacing between notes (and the number of `-` characters between fretted notes) and since tabs found in the wild are all over the place in this respect, YMMV. Note that to strike a balance between readability and compactness, **gtrsnipe** uses a logarithmic spacing algorithm when generating ASCII tabs from MIDI to try and encode as much of this information as possible given the format, so tabs that were originally created by **gtrsnipe** will often fare better in the final playback of a generated midi than ones posted to usenet in the 1990's. 

By default **gtrsnipe** will try to infer hammer-on/pull-off performance technique articulations based on the timing of the notes. You can disable this (for straight-picking transcriptions) with `--no-articulations`. Additionally, there is a `--single-string` option for transcriptions that might be best represented on one string with taps/hammer-ons/pull-offs. Best for pieces/segments you know should be played in this manner.

**gtrsnipe** tries to intelligently find the best neck and fingering positions using a note to fretboard mapper and a scoring algorithm that is unavoidably shaped by my *subjective* opinions and skills as a player but it  does its best to avoid *objectively* impossible fingerings.

The `--nudge` option exists because MIDI track start times can sometimes also be all over the place and is designed to help you make your ascii TAB more visually appealing, though not necessarily accurate in terms of how many "rest" measures there may be before the transcription begins. See example usage below.

## Installation

```
git clone https://github.com/scottvr/gtrsnipe
cd gtrsnipe
python -mvenv .venv
```

on Windows:

```
.venv\Scripts\activate
```

bash:

```
. .venv/bin/activate
```

Then, 

```
pip install .
```


## Usage Help

```
usage: gtrsnipe [-h] [--nudge NUDGE] [--track TRACK] [--no-articulations] [--staccato] [--debug] input_file output_file

Convert music files between binary MIDI .mid and ASCII .tab .vex, and .abc notation formats, in any direction.

positional arguments:
  input_file          Path to the input music file
  output_file         Path to save the output music file

options:
  -h, --help          show this help message and exit
  --nudge NUDGE       An integer to shift the transcription's start time to the right. Each unit
                      corresponds to roughly a 16th note.
  -y, --yes           Overwrite the output file if it already exists.
  --track TRACK       The track number (1-based) to select from a multi-track MIDI file. 
                      If not set, all tracks are processed. 
                      For a multitrack midi, you will want to select a single instrument track to transcribe.
  --no-articulations  Transcribe with no legato, taps, hammer-ons, pull-offs, etc.
  --staccato          Do not extend note durations to the start of the next note for a sustained feel,
                      instead giving each note an 1/8 note duration. Primarily for tab-to-MIDI conversions.
  --single-string {1,2,3,4,5,6}
                      Force all notes onto a single string (1-6, high e to low E). Ideal for transcribing legato/tapping runs.
  --debug             Enable detailed debug logging messages.

```

### Examples

```
$ gtrsnipe MrCrowley.mid mrcrowley-organ.tab --track 5
Converting 'MrCrowley.mid' (mid) to 'mrcrowley-organ.tab' (tab)...
--- Selecting track 5 of 7 ---
--- Chord-Aware Mapper initialized. ---
Successfully saved to mrcrowley-organ.tab

$ cat ./mrcrowley-organ.tab
// Title: MrCrowley
// Tempo: 106.0 BPM
// Time: 4/4
// Tuning: STANDARD

e|--1----------------|--0--------------------|--1----------------|--3--------------------|--5----------------|
B|--3----------------|--1--------------------|--1----------------|--5--------------1---p0|--5----------------|
G|--2----------------|--2--------------2---p0|--2-----0---h2----4|--5--------------------|--5-----4---h5----7|
D|--0-----2---h3----5|--2-----2--------------|--3----------------|--5-----5--------------|--7----------------|
A|-------------------|--0---------0----------|--3----------------|--3---------3----------|--7----------------|
E|-------------------|-----------------------|--1----------------|-----------------------|--5----------------|

e|--7-------------|-------------1--|--3----1----0----1|--5-------------|--0-------------|--1----------------|
B|--8-------------|--1-----3----1--|--3----1----0----1|--6-------------|----------------|--3----------------|
G|--9-------------|--2-----3----5--|--7----5----4----5|--7-------------|----------------|--2----------------|
D|--9----9--------|-------------3--|--5----3----2----3|--7-------------|--11-----3---p2-|--0-----2---h3----5|
A|--7---------7---|--0-----1-------|------------------|--0-------------|----------------|-------------------|
E|----------------|-------------1--|--3----1----0----1|----------------|----------------|-------------------|

e|--0--------------------|--1----------------|--3--------------------|--5----------------|--7-------------|
B|--1--------------------|--1----------------|--5--------------1---p0|--5----------------|--8-------------|
G|--2--------------2---p0|--2-----0---h2----4|--5--------------------|--5-----4---h5----7|--9-------------|
D|--2-----2--------------|--3----------------|--5-----5--------------|--7----------------|--9----9--------|
A|--0---------0----------|--3----------------|--3---------3----------|--7----------------|--7---------7---|
E|-----------------------|--1----------------|-----------------------|--5----------------|----------------|

e|-------------1--|--3----1----0----1|--5-------------|--0-------------|
B|--1-----3----1--|--3----1----0----1|--6-------------|----------------|
G|--2-----3----5--|--7----5----4----5|--7-------------|----------------|
D|-------------3--|--5----3----2----3|--7-------------|--11------------|
A|--0-----1-------|------------------|--0-------------|----------------|
E|-------------1--|--3----1----0----1|----------------|----------------|

```


```
$ gtrsnipe SmellsLikeTeenSpirit.mid --track 6 teenspirit-bass.tab --no-articulations --nudge 14
Converting 'SmellsLikeTeenSpirit.mid' (mid) to 'teenspirit-bass.tab' (tab)...
--- Selecting track 6 of 11 ---
--- Nudging all events forward by 3.5 beats ---
--- Chord-Aware Mapper initialized. ---
Successfully saved to teenspirit-bass.tab

$ cat teenspirit-bass.tab
// Title: SmellsLikeTeenSpirit
// Tempo: 110.0 BPM
// Time: 4/4
// Tuning: STANDARD

e|----------------|----------------|----------------|----------------|----------------|----------------|
B|----------------|----------------|----------------|----------------|----------------|----------------|
G|----------------|----------------|----------------|----------------|----------------|----------------|
D|----------------|----------------|----------------|----------------|----------------|----------------|
A|----------------|----------------|----------------|----------------|----------------|----------------|
E|----------------|----------------|----------------|----------------|----------------|----------------|

e|---------------------------------|---------------------------------|---------------------------------|
B|---------------------------------|---------------------------------|---------------------------------|
G|---------------------------------|---------------------------------|---------------------------------|
D|---------------------------------|---------------------------------|---------------------------------|
A|------------------------1---1----|------------------------4---4----|------------------------1---1----|
E|--1----1--1----1--1--1----------1|--4----4--4----4--4--4----------4|--1----1--1----1--1--1----------1|

e|---------------------------------|---------------------------------|---------------------------------|
B|---------------------------------|---------------------------------|---------------------------------|
G|---------------------------------|---------------------------------|---------------------------------|
D|---------------------------------|---------------------------------|---------------------------------|
A|------------------------4---4----|------------------------1---1----|------------------------4---4----|
E|--4----4--4----4--4--4----------4|--1----1--1----1--1--1----------1|--4----4--4----4--4--4----------4|

e|---------------------------------|---------------------------------|-------------------------------|
B|---------------------------------|---------------------------------|-------------------------------|
G|---------------------------------|---------------------------------|-------------------------------|
D|---------------------------------|---------------------------------|-------------------------------|
A|------------------------1---1----|------------------------4---4----|------------------1---1---1---1|
E|--1----1--1----1--1--1----------1|--4----4--4----4--4--4----------4|--1---1---1---1----------------|

