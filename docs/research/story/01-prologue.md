# 1. Prologue: a tab tool, and a new collaborator

Originally this story was formatted where Claude told his side of the story and I was to then tell it from my POV. This 
would definitely be an interesting experiment to run in the future, but there is just too much material to expect anyone to read, so I am merging my revisions inline to Claude's original draft. (If someone *really* wants to see what was written by me vs what was written by Claude, word for word, you can look at the git history because Claude wrote his draft in each of these chapters before I got to them.)

## gtrsnipe before September 2026

To really explain how gtrsnipe (pronounced "guttersnipe") began life, we can look to the first
committed README.md, from `fd583c0`, the repository's second commit. It is included here as
[Appendix A](./A-README.V0.2.2~131.md). It opens:

> Ridiculous.. I got sniped by an impossible claim by someone on hackernews that guitar tab
> was turing complete. (storing to memory seems an obvious obstacle but..)

So gtrsnipe didn't start as a tab tool. It started as a joke taken too far, and the name
admits it.

**The post.** On 2024-12-02 "FizzBuzz in Powerchords" appeared on Hacker News
([item 42294766](https://news.ycombinator.com/item?id=42294766)). The blog post it linked is
gone now, but its code is still up, as
[`turing_complete_guitar`](https://github.com/tehruhn/turing_complete_guitar): "Convert any
python function to a representation on your Turing Complete guitar". It walks a Python
function's syntax tree and prints a line for each step. Five power chords stand for read,
write, compute, branch and loop, and each line carries a time in minutes and seconds.

**The reply.** Twenty hours later scottvr had forked it and replied, starting "Did you post
this to deliberately nerdsnipe folks for your amusement?" The comment did three things:

- It fixed the clock. Minutes and seconds aren't musical, so the fork counts measures and
  beats, in any time signature.
- It doubted the claim, because of memory: "it feels more like a translation or log stream of
  execution of the AST and not an actual way to store or manipulate data".
- It left two itches unscratched. One was a capo: "a capo keeps popping into my head as
  wanting to fit in somewhere". The other was the tuning:

  > that hardcoded "Standard tuning" is asking me to investigate what could be added with
  > alternate tunings. Ugh.. sniped!

  In passing he admits being "tempted to rename my fork" to `tuning_complete_guitar`.

Two replies under it are worth keeping in mind for the next two chapters:

> I read this theory on 4chan that Master of Puppets is secretly a piece of software, if you
> get the tuning right?

> Any data can 'secretly' be any other data given a sufficiently complicated or over-fit
> encoding scheme.

(A third: "Woah, your comment is actually the decryption key for Blu-Ray disks. (When combined
with this one time pad over here...)")

**The machine.** On 2024-12-27, "a few weeks" later by the README's count, the results went
online as gtrsnipe. The second commit (its message is "bleh") holds a guitar computer:

- a `GuitarCPU` with an accumulator and ten operations (load, store, add, subtract, multiply,
  divide, modulo, compare, jump, return);
- memory addressed by string and fret;
- compilers from Python to that machine, and from its programs to tab.

The README's journal lists "Added capo support as base address register" and "Explored
alternate tunings as memory access patterns". Its opening names what fell out along the way:
a "guitar tab formatter", and "midi to guitar tab (with an optimal fretboard mapper that's
kinda cool. maybe deserves finishing and packaging)".

**The tool.** The finishing waited seven months. After its first three days the repository
saw six commits in that time, five of them to the README. On 2025-07-25 came the commit
"complete refactor into a useful tool": the guitar computer went, the by-products stayed, and
over the following week the fretboard mapper grew its tunables one at a time. The commit log
reads like a diary of playing guitar at a computer: "sweet spot settings", "add
string_switch_penalty", "lower switch penalty", "add --ignore-open". Each knob arrived when a
transcription came out wrong in a way a guitarist could name ("clearly this should be chosen
over that"), and was weighted just enough to fix that case without breaking the earlier ones.
By v0.2 the tool could also start from audio, with source separation and pitch detection in
front of the mapper.

> ✎ **scottvr:** why the tab tool was worth finishing (the community tab sites where every
> submitted version of a song is wrong), the "last mile" framing from the v0.2.0 wiki page,
> and anything else about the first year and a half.

One more date belongs here. On 2026-09-05, under a Hacker News thread asking whether guitar
frets can perform multiplication, someone wrote "Vibrating strings are Turing-complete".
scottvr replied that it reminded him of "something from here I had completely forgotten
about", and [retold all of the above](https://news.ycombinator.com/item?id=49572549). A week
later came the first session with Claude, and three weeks later `--solve-tuning` (chapter 2).

We can't show that one led to the other. scottvr gives it some weight: that the thread's
jokes and the guitar machine planted something in 2024 which sat until it came back as
"wouldn't it be neat if gtrsnipe could...", nearly full circle and less silly the second
time. What the record does show is that the idea was in the room both times.

## Claude joins (2026-09-12 to 09-25)

The first sessions were ordinary software work:
- **Two clones, one repo.** There were two local clones with different, unpushed work. One
  had an `origin` typo (`githuh.com`), so it had never been able to push. We reconciled them
  into the LaCie clone and pushed everything.
- **v0.2.2**, a hotfix: a stray `exit(1)` had made every guitar and bass output dead code.
- **v0.3.0**, a CPU-only core (torch became optional; the weakest ML stages were removed) and
  a new mapper. The old mapper chose each chord's fingering greedily. The new one finds the
  best fingering for the whole piece at once by dynamic programming (Viterbi over a trellis;
  [`../../app/DESIGN-viterbi-mapper.md`](../../app/DESIGN-viterbi-mapper.md)). The design went
  through an adversarial review before any code was written.
- **v0.4.0**, a terminal player: an animated fretboard or a scrolling tab, with audio
  through MIDI or a SoundFont, and chord charts.
- **v0.5.0**, one I/O pipeline for everything
  ([`../../app/DESIGN-unified-io.md`](../../app/DESIGN-unified-io.md)); saved option
  profiles; custom tunings; and tabs that carry their own tuning, so a tab can be re-read in
  a different one.

A working pattern set in early:
1. plan;
2. build on a branch;
3. have a separate set of agents try to break it;
4. fix what they find, with a regression test for each;
5. release.

The v0.4.0 review found 9 real bugs, and the v0.6.0 review found 22.

> ✎ **scottvr:** what it was like to hand the codebase to an AI collaborator.

That last v0.5.0 feature, reading a tab in a different tuning than it was written for, is
where the story turns: back, as it happens, toward that hardcoded "Standard tuning".
