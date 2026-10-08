# 1. Prologue: a tab tool, and a new collaborator

Originally this story was formatted where Claude told his side of the story and I was to then tell it from my POV. While this 
would definitely be an interesting experiment to run in the futurek, but there is just too much material to expect anyone to read, so I am merging my revisions inline to CLaude's original draft. (If someone *really* wants to see what was written by me vs what was written by Claude, qword for word, you can look at the git history because Claude wrote his draft in each of these chapters before I got to them.)

## gtrsnipe before September 2026

To really explain how gtrsnipe (pronounced "Guttersnipe") began life, we can look to the first commited README.md from `fd583c0`
It is included here as [Appendix A](./A-README.V0.2.2~131.md). 

started on 2024-12-27 as a way to get from MIDI to readable ASCII guitar tab. On
2025-07-25 came the commit "complete refactor into a useful tool", and over the following week
the fretboard mapper grew its tunables one at a time. The commit log reads like a diary of
playing guitar at a computer: "sweet spot settings", "add string_switch_penalty", "lower switch
penalty", "add --ignore-open". Each knob arrived when a transcription came out wrong in a way a
guitarist could name ("clearly this should be chosen over that"), and was weighted just enough
to fix that case without breaking the earlier ones. By v0.2 the tool could also start from
audio, with source separation and pitch detection in front of the mapper.

> ✎ **scottvr:** why gtrsnipe (the community tab sites where every submitted version of a
> song is wrong), the "last mile" framing from the v0.2.0 wiki page, and anything else about
> the first year and a half.

## Claude joins (2026-09-12 to 09-25)

The first sessions were ordinary software work:
- **Two clones, one repo.** There were two local clones with different, unpushed work. One
  had an `origin` typo (`githuh.com`), so it had never been able to push. They were reconciled
  into the LaCie clone, and everything was pushed.
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

That last v0.5.0 feature, reading a tab in a different tuning than it was written for, is
where the story turns.

## scottvr's account

> ✎ the first year and a half, and what it was like to hand the codebase to an AI collaborator.
